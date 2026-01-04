from django.db.transaction import atomic
from django.db.models import Model, CharField, DateField, ForeignKey, PositiveIntegerField, CASCADE, PROTECT, SET_NULL, BooleanField, UniqueConstraint


def generate_challan(prefix_name, seq, year):
    initials = ''.join(w[0] for w in prefix_name.split()[:4]).upper()
    y = year % 100
    return f"{initials}/{seq:03d}/{y:02d}-{y+1:02d}"


class PrinterModel(Model):
    name = CharField(max_length=300, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "printer_model"
        verbose_name_plural = "printer_models"


class Store(Model):
    name = CharField(max_length=200, unique=True)
    address = CharField(max_length=500)
    
    def __str__(self):
        return self.name

    class Meta:
        db_table = "store"
        verbose_name_plural = "stores"


class Vendor(Model):
    name = CharField(max_length=200, unique=True)
    address = CharField(max_length=500)
    mobile = CharField(max_length=20)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "vendor"
        verbose_name_plural = "vendors"


class Customer(Model):
    name = CharField(max_length=200, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "customer"
        verbose_name_plural = "customers"


class CustomerAddress(Model):
    customer = ForeignKey(Customer, on_delete=CASCADE, related_name="addresses")
    address = CharField(max_length=500)
    mobile = CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        return f"{self.customer.name} - {self.address}"

    class Meta:
        db_table = "customer_address"
        verbose_name_plural = "customer_addresses"
        constraints = [
            UniqueConstraint(
                fields=["customer", "address"],
                name="unique_address_per_customer"
            )
        ]


class Purchase(Model):
    challan_no = CharField(max_length=50, unique=True, null=True, blank=True)
    vendor = ForeignKey(Vendor, on_delete=PROTECT, related_name="purchases")
    store = ForeignKey(Store, on_delete=PROTECT, related_name="purchases")
    date = DateField()

    def __str__(self):
        return f"Purchased from {self.vendor.name} on {self.date}"

    class Meta:
        db_table = "purchase"
        verbose_name_plural = "purchases"
    
    def save(self, *args, **kwargs):
        if self.pk:
            return super().save(*args, **kwargs)
        with atomic():
            year = self.date.year
            last = Purchase.objects.select_for_update().filter(date__year=year).order_by('-id').first()
            seq = int(last.challan_no.split('/')[1]) + 1 if last and last.challan_no else 1
            self.challan_no = generate_challan(self.vendor.name,seq,year)
            super().save(*args, **kwargs)


class PurchaseItem(Model):
    purchase = ForeignKey(Purchase, on_delete=CASCADE, related_name="items")
    printer_model = ForeignKey(PrinterModel, on_delete=PROTECT)
    quantity = PositiveIntegerField()

    class Meta:
        unique_together = ("purchase", "printer_model")
        db_table = "purchase_item"
        verbose_name_plural = "purchase_items"

    def __str__(self):
        return f"{self.quantity} x {self.printer_model.name} for Purchase - {self.purchase.challan_no}"
    
    def save(self, *args, **kwargs):
        creating = self.pk is None
        with atomic():
            super().save(*args, **kwargs)
            if creating:
                for _ in range(self.quantity):
                    PrinterUnit.objects.create(
                        printer_model=self.printer_model,
                        status=PrinterUnit.STATUS_INSTORE,
                        purchase_item=self,
                        store=self.purchase.store,
                    )


class PrinterUnit(Model):
    STATUS_INSTORE = "INSTORE"
    STATUS_RENTED = "RENTED"
    STATUS_SCRAPPED = "SCRAPPED"

    STATUS_CHOICES = [
        (STATUS_INSTORE, "In-store"),
        (STATUS_RENTED, "Rented"),
        (STATUS_SCRAPPED, "Scrapped"),
    ]

    serial_number = CharField(max_length=200, unique=True, blank=True, null=True)
    printer_model = ForeignKey(PrinterModel, on_delete=PROTECT, related_name="units")
    status = CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_INSTORE)
    purchase_item = ForeignKey(PurchaseItem, null=True, blank=True, on_delete=SET_NULL, related_name="purchased_printer_units")
    store = ForeignKey(Store, null=True, blank=True, on_delete=SET_NULL, related_name="store_printer_units")
    customer_address = ForeignKey(CustomerAddress, null=True, blank=True, on_delete=SET_NULL, related_name="rented_printer_units")


    class Meta:
        db_table = "printer_unit"
        verbose_name_plural = "printer_units"

    def __str__(self):
        return self.serial_number or f"Unit #{self.pk}"


class Rental(Model):
    challan_no = CharField(max_length=100, null=True, blank=True, unique=True)
    challan_date = DateField()
    order_no = CharField(max_length=100, null=True, blank=True)
    order_date = DateField()
    store = ForeignKey(Store, on_delete=PROTECT, related_name="rentals")
    customer_address = ForeignKey(CustomerAddress, on_delete=PROTECT, related_name="rentals")

    class Meta:
        db_table = "rental"
        verbose_name_plural = "rentals"

    def __str__(self):
        return self.challan_no

    def save(self, *args, **kwargs):
        if self.pk:
            return super().save(*args, **kwargs)
        with atomic():
            year = self.challan_date.year
            last = Rental.objects.select_for_update().filter(challan_date__year=year).order_by('-id').first()
            seq = int(last.challan_no.split('/')[1]) + 1 if last and last.challan_no else 1
            self.challan_no = generate_challan(self.customer_address.customer.name,seq,year)
            super().save(*args, **kwargs)


class RentalUnit(Model):
    rental = ForeignKey(Rental, on_delete=CASCADE, related_name="units")
    printer_unit = ForeignKey(PrinterUnit, on_delete=PROTECT, related_name="rental_entries")

    class Meta:
        db_table = "rental_unit"
        verbose_name_plural = "rental_units"

    def __str__(self):
        return f"{self.printer_unit.serial_number} → Rental #{self.rental.challan_no}"
    
    def save(self, *args, **kwargs):
        creating = self._state.adding
        with atomic():
            if creating:
                locked_unit = PrinterUnit.objects.select_for_update().get(pk=self.printer_unit.pk)
                if locked_unit.status != PrinterUnit.STATUS_INSTORE:
                    raise ValueError("This unit is not available for rent.")
                locked_unit.status = PrinterUnit.STATUS_RENTED
                locked_unit.store = None
                locked_unit.customer_address = self.rental.customer_address
                locked_unit.save(update_fields=["status","store","customer_address"])
            super().save(*args, **kwargs)


class RentalReturn(Model):
    challan_no = CharField(max_length=100, null=True, blank=True, unique=True)
    challan_date = DateField()
    order_no = CharField(max_length=100, null=True, blank=True)
    order_date = DateField(null=True, blank=True)
    customer_address = ForeignKey(CustomerAddress, on_delete=PROTECT, related_name="rental_returns")
    store = ForeignKey(Store, on_delete=PROTECT, related_name="rental_returns" )

    class Meta:
        db_table = "rental_return"
        verbose_name_plural = "rental_returns"

    def __str__(self):
        return self.challan_no
    
    def save(self, *args, **kwargs):
        if self.pk:
            return super().save(*args, **kwargs)
        with atomic():
            year = self.challan_date.year
            last = RentalReturn.objects.select_for_update().filter(challan_date__year=year).order_by('-id').first()
            seq = int(last.challan_no.split('/')[1]) + 1 if last and last.challan_no else 1
            self.challan_no = generate_challan(self.customer_address.customer.name,seq,year)
            super().save(*args, **kwargs)


class RentalReturnUnit(Model):
    rental_return = ForeignKey(RentalReturn, on_delete=CASCADE, related_name="rental_returned_units")
    printer_unit = ForeignKey(PrinterUnit, on_delete=PROTECT, related_name="rental_return_entries")
    scrapped = BooleanField(default=False)

    class Meta:
        db_table = "rental_return_unit"
        verbose_name_plural = "rental_return_units"

    def __str__(self):
        return f"{self.printer_unit.serial_number} → Rental #{self.rental_return.challan_no}"

    def save(self, *args, **kwargs):
        creating = self._state.adding
        with atomic():
            super().save(*args, **kwargs)
            if creating:
                unit = self.printer_unit
                if self.scrapped:
                    unit.status = PrinterUnit.STATUS_SCRAPPED
                    unit.store = None
                    unit.customer_address = None
                else:
                    unit.status = PrinterUnit.STATUS_INSTORE
                    unit.store = self.rental_return.store
                    unit.customer_address = None
                unit.save(update_fields=["status", "store", "customer_address"])

