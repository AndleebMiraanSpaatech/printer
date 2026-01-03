from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from api.models import PrinterModel, Store, Vendor, Customer, CustomerAddress, PrinterUnit, Purchase, Rental, RentalUnit, RentalReturn, RentalReturnUnit
import json
from collections import defaultdict
from django.db.models import Count  
from itertools import chain

master_data_models = {
    'printer-model': PrinterModel,
    'store': Store,
    'vendor': Vendor,
}
page_size = 10
def paginated(qs, page_no):
    return qs[(page_no - 1) * page_size : page_no * page_size]

def login(request):
    if request.user.is_authenticated:
        return redirect('frontend:home')
    return render(request, "login.html")

def signup(request):
    return render(request, "signup.html")

@login_required
def home(request):
    return render(request, "home.html",{})

# ----------------- Master Data Views -----------------

@login_required
def master_data_list(request, kebab_case_model):
    page_no = int(request.GET.get('page_no', "1"))
    Model = master_data_models[kebab_case_model]
    return render(request, "master_data/list.html", {   
        "objects": paginated(Model.objects.order_by("id"),page_no),
        "model": Model,
        "page_no": page_no,
        "count": Model.objects.count()
    })

@login_required
def master_data_add(request, kebab_case_model):
    Model = master_data_models[kebab_case_model]
    foreign_keys = {
        f.name: f.remote_field.model.objects.all()
        for f in Model._meta.get_fields()
        if f.many_to_one and f.concrete
    }
    return render(request, "master_data/add.html", {
        "model": Model,
        "foreign_keys": foreign_keys,
    })

@login_required
def master_data_edit(request, kebab_case_model):
    Model = master_data_models[kebab_case_model]
    foreign_keys = {
        f.name: f.remote_field.model.objects.all()
        for f in Model._meta.get_fields()
        if f.many_to_one and f.concrete
    }
    return render(request, "master_data/edit.html", {
        "model": Model,
        "edit_object": Model.objects.get(id=request.GET.get("id")),
        "foreign_keys": foreign_keys,
    })

@login_required
def printer_unit_list(request):
    page_no = int(request.GET.get("page_no", "1"))
    status = request.GET.get("status")
    serial_no = request.GET.get("serial_no", "").strip()
    all_units_qs = PrinterUnit.objects.select_related(
        "printer_model",
        "store",
        "customer_address",
        "customer_address__customer",
    ).order_by("id")
    if status:
        all_units_qs = all_units_qs.filter(status=status)
    if serial_no:
        all_units_qs = all_units_qs.filter(serial_number__icontains=serial_no)
    paginated_units = paginated(all_units_qs, page_no)
    for unit in paginated_units:
        if unit.status == PrinterUnit.STATUS_INSTORE and unit.store:
            unit.location = unit.store.name
            unit.address = unit.store.address
        elif unit.status == PrinterUnit.STATUS_RENTED and unit.customer_address:
            unit.location = unit.customer_address.customer.name
            unit.address = unit.customer_address.address
        else:
            unit.location = "—"
            unit.address = "—"

    return render(request, "master_data/printer_unit/list.html", {
        "objects": paginated_units,
        "page_no": page_no,
        "count": all_units_qs.count(),
        "status": status,
        "serial_no": serial_no,
    })

@login_required
def printer_unit_add(request):
    printer_models = PrinterModel.objects.all().order_by("name")
    stores = Store.objects.all().order_by("name")
    
    return render(request, "master_data/printer_unit/add.html", {
        "printer_models": printer_models,
        "stores": stores,
    })

@login_required
def printer_unit_edit(request):
    unit_id = request.GET.get("id")
    unit = PrinterUnit.objects.select_related("printer_model", "store").get(id=unit_id)
    
    return render(request, "master_data/printer_unit/edit.html", {
        "edit_object": unit,
        "printer_models": PrinterModel.objects.all().order_by("name"),
        "stores": Store.objects.all().order_by("name"),
    })
    
@login_required
def customer_list(request):
    page_no = int(request.GET.get("page_no", "1"))
    all_customers_qs = Customer.objects.prefetch_related("addresses").order_by("id")
    paginated_customers = paginated(all_customers_qs, page_no)
    return render(request, "master_data/customer/list.html", {
        "objects": paginated_customers,
        "page_no": page_no,
        "count": all_customers_qs.count(),
    })
    
@login_required
def customer_add(request):
    return render(request, "master_data/customer/add.html", {})

@login_required
def customer_edit(request):
    customer_id = request.GET.get("id")
    customer = Customer.objects.prefetch_related("addresses").get(id=customer_id)
    return render(request, "master_data/customer/edit.html", {
        "customer": customer,
    })

@login_required
def purchase_list(request):
    page_no = int(request.GET.get("page_no", "1"))
    all_purchases_qs = Purchase.objects.select_related("vendor","store").prefetch_related("items__purchased_printer_units").order_by("-date")
    paginated_purchases = paginated(all_purchases_qs,page_no)
    for purchase in paginated_purchases:
        purchase.printer_count = sum(len(item.purchased_printer_units.all())for item in purchase.items.all())
    return render(request, "purchase/list.html", {
        "objects": paginated_purchases,
        "page_no": page_no,
        "count": all_purchases_qs.count(),
    })
    
@login_required
def purchase_add(request):
    vendors = Vendor.objects.all().order_by("name")
    stores = Store.objects.all().order_by("name")
    printer_models = list(PrinterModel.objects.all().order_by("name").values("id", "name"))

    return render(request, "purchase/add.html", {
        "vendors": vendors,
        "stores": stores,
        "printer_models": json.dumps(printer_models),
    })

@login_required
def purchase_item_list(request, purchase_id):
    purchase = Purchase.objects.prefetch_related('items__printer_model').get(id=purchase_id)
    items = purchase.items.all()
    return render(request, "purchase/purchase_item/list.html", {
        "purchase": purchase,
        "items": items,
    })

@login_required
def rental_list(request):
    page_no = int(request.GET.get("page_no", "1"))
    all_rentals_qs = Rental.objects.select_related("store", "customer_address", "customer_address__customer"
        ).order_by("-challan_date")
    paginated_rentals = paginated(all_rentals_qs, page_no)
    return render(request, "rental/list.html", {
        "objects": paginated_rentals,
        "page_no": page_no,
        "count": all_rentals_qs.count(),
    })

@login_required
def rental_add(request):
    stores = Store.objects.all().order_by("name")
    customers = Customer.objects.all().order_by("name")
    customer_addresses = CustomerAddress.objects.all()
    printer_models = PrinterModel.objects.all().order_by("name")
    printer_units = PrinterUnit.objects.order_by("serial_number")
    return render(request, "rental/add.html", {
        "stores": stores,
        "customers": customers,
        "customer_addresses": customer_addresses,
        "printer_models": printer_models,
        "printer_units": printer_units,
    })

@login_required
def rental_item_list(request, rental_id):
    rental = Rental.objects.get(id=rental_id)
    printer_units = PrinterUnit.objects.select_related('printer_model').filter(rental_entries__rental_id=rental_id)
    printer_dict = {}
    for unit in printer_units:
        printer_dict.setdefault(unit.printer_model.name, []).append(unit.serial_number)
    return render(request, "rental/rental_item/list.html", {
        "rental": rental,
        "printer_dict": printer_dict,
    })

@login_required
def rental_challan_pdf(request, rental_id):
    rental = Rental.objects.get(id=rental_id)
    printer_units = PrinterUnit.objects.select_related('printer_model').filter(rental_entries__rental_id=rental_id)
    printer_dict = {}
    for unit in printer_units:
        printer_dict.setdefault(unit.printer_model.name, []).append(unit.serial_number)
    return render(request, "rental/rental_challan_pdf.html", {
        "rental": rental,
        "printer_dict": printer_dict,
    })
    
@login_required
def rental_return_list(request):
    page_no = int(request.GET.get("page_no", "1"))
    all_rental_returns_qs = RentalReturn.objects.select_related("store","customer_address","customer_address__customer",
        ).order_by("-challan_date")
    paginated_returns = paginated(all_rental_returns_qs, page_no)
    return render(request, "rental_return/list.html", {
        "objects": paginated_returns,
        "page_no": page_no,
        "count": all_rental_returns_qs.count(),
    })

@login_required
def rental_return_add(request):
    stores = Store.objects.all().order_by("name")
    customers = Customer.objects.all().order_by("name")
    customer_addresses = CustomerAddress.objects.all()

    return render(request, "rental_return/add.html", {
        "stores": stores,
        "customers": customers,
        "customer_addresses": customer_addresses,
    })

@login_required
def rental_return_item_list(request, rental_return_id):
    rental_return = RentalReturn.objects.get(id=rental_return_id)
    returned_units = RentalReturnUnit.objects.select_related(
        'printer_unit', 'printer_unit__printer_model'
    ).filter(rental_return_id=rental_return_id)
    printer_dict = {}
    for rru in returned_units:
        unit = rru.printer_unit
        printer_dict.setdefault(unit.printer_model.name, []).append(
            (unit.serial_number, rru.scrapped)
        )
    return render(request, "rental_return/rental_return_item/list.html", {
        "rental_return": rental_return,
        "printer_dict": printer_dict,
    })

@login_required
def inventory_in_store(request):
    units = PrinterUnit.objects.select_related('printer_model', 'store').filter(
        status=PrinterUnit.STATUS_INSTORE).order_by('printer_model__name', 'store__name')
    printer_dict = {}
    for unit in units:
        printer_dict.setdefault(unit.printer_model.name, []).append(
            (unit.store.name, unit.store.address, 1))
    result = {}
    for model, lst in printer_dict.items():
        store_map = {}
        for store, addr, _ in lst:
            store_map[store] = store_map.get(store, (addr, 0))
            store_map[store] = (addr, store_map[store][1]+1)
        result[model] = [(s, a, q) for s, (a, q) in store_map.items()]
    return render(request, "inventory_in_store/list.html", {"printer_dict": result})

@login_required
def inventory_on_rentt(request):
    units = PrinterUnit.objects.select_related('printer_model', 'customer_address', 'customer_address__customer'
        ).filter(status=PrinterUnit.STATUS_RENTED).order_by('printer_model__name', 'customer_address__customer__name')
    printer_dict = {}
    for unit in units:
        model = unit.printer_model.name
        customer = unit.customer_address.customer.name
        address = unit.customer_address.address
        printer_dict.setdefault(model, []).append((customer, address, 1))
    result = {}
    for model, lst in printer_dict.items():
        cust_map = {}
        for cust, addr, _ in lst:
            cust_map[cust] = cust_map.get(cust, (addr, 0))
            cust_map[cust] = (addr, cust_map[cust][1] + 1)
        result[model] = [(c, a, q) for c, (a, q) in cust_map.items()]
    return render(request, "inventory_on_rent/list.html", {"printer_dict": result})

@login_required
def inventory_on_rent(request):
    data = defaultdict(lambda: defaultdict(dict))
    for r in PrinterUnit.objects.filter(status=PrinterUnit.STATUS_RENTED).values(
        'printer_model__name','customer_address__customer__name','customer_address__address').annotate(qty=Count('id')):
        data[r['printer_model__name']][r['customer_address__customer__name']][r['customer_address__address']] = r['qty']
    rows = [{"sno": i+1 if j==0 and k==0 else None, "model": m if j==0 and k==0 else None,
            "model_rowspan": sum(len(v) for v in c.values()) if j==0 and k==0 else None,
            "customer": u if k==0 else None, "customer_rowspan": len(a) if k==0 else None,
            "address": ad, "qty": q}
            for i,(m,c) in enumerate(data.items())
            for j,(u,a) in enumerate(c.items())
            for k,(ad,q) in enumerate(a.items())]
    return render(request, "inventory_on_rent/list.html", {"rows": rows})

@login_required
def inventory_by_status(request):
    units = PrinterUnit.objects.select_related('printer_model').all()
    printer_dict = {}
    for unit in units:
        model = unit.printer_model.name
        status = unit.status
        printer_dict.setdefault(model, {"INSTORE":0, "RENTED":0, "SCRAPPED":0})
        printer_dict[model][status] += 1
    result = [(model, counts["INSTORE"], counts["RENTED"], counts["SCRAPPED"]) for model, counts in printer_dict.items()]
    return render(request, "inventory_by_status/list.html", {"printer_list": result})