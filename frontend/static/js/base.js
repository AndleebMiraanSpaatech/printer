$(function () {
    
    // ajax form submission
    $(document).on("submit", ".ajax-form", (e) => {
        e.preventDefault();
        const f = e.target;
        if (!f.checkValidity()) return alert("Please fill all fields.");

        const m = f.dataset.method || "POST";
        const u = f.dataset.url;
        const r = f.dataset.redirect;
        const em = f.dataset.errorMessage;
        const c = f.dataset.csrf;

        $.ajax({
            type: m,
            url: u,
            data: new FormData(f),
            processData: false,
            contentType: false,
            headers: { "X-CSRFToken": c },
            success: (res) => {
                if (r) return (location.href = r);
            },
            error: () => alert(em || "Error submitting form."),
        });
    });

    // universal Choices init
    $("select[data-choices]").each(function () {
        new Choices(this, {
            searchEnabled: true,
            itemSelectText: "",
            placeholder: true,
            placeholderValue: this.dataset.placeholder || "Select",
            shouldSort: false,
        });
    });

    // universal delete handler
    $(document).on("click", ".delete-btn", function () {
        const id = $(this).data("id");
        const modelUrl = $(this).data("model-url") || "item";
        const modelName = $(this).data("model-name") || "item";
        if (!confirm(`Are you sure you want to delete this ${modelName}?`)) return;

        $.ajax({
            url: `/api/${modelUrl}/${id}/`,
            type: "DELETE",
            headers: { "X-CSRFToken": $(this).data("csrf") },
            success: () => location.reload(),
            error: () => alert(`Failed to delete ${modelName}.`),
        });
    });

    flatpickr(".flatpickr", { dateFormat: "Y-m-d", maxDate: "today" });
});

function pagination(pageNo, count) {
    const urlParams = new URLSearchParams(window.location.search);
    function liHTML(value, isDisabled = false, isCurrentPage = false) {
        let newParams = new URLSearchParams(urlParams);
        if (!isNaN(value)) {
            newParams.set("page_no", value);
        } else if (value === "Previous") {
            newParams.set("page_no", pageNo - 1);
        } else if (value === "Next") {
            newParams.set("page_no", pageNo + 1);
        }
        return `<li class="page-item${isDisabled ? ' disabled' : ''}${isCurrentPage ? ' active' : ''}">
                    <a class="page-link" href="?${newParams.toString()}">${value}</a>
                </li>`;
    }

    const pageCount = Math.ceil(count / 10);
    if (pageCount === 0) {
        $(".pagination").html('');
        return;
    }

    let arr = [
        liHTML("Previous", pageNo === 1),
        liHTML(1, false, pageNo === 1),
        liHTML("Next", pageNo === pageCount)
    ];

    if (pageCount > 1 && pageCount < 8) {
        for (let i = 2; i <= pageCount; i++) arr.splice(i, 0, liHTML(i, false, i === pageNo));
    } else if (pageCount > 7) {
        if (pageNo <= 3) {
            for (let i = 2; i <= 5; i++) arr.splice(i, 0, liHTML(i, false, i === pageNo));
            arr.splice(6, 0, liHTML("...", true));
            arr.splice(7, 0, liHTML(pageCount, false, pageCount === pageNo));
        } else if (pageNo > pageCount - 3) {
            arr.splice(2, 0, liHTML("...", true));
            for (let i = pageCount; i > pageCount - 5; i--) arr.splice(3, 0, liHTML(i, false, i === pageNo));
        } else {
            arr.splice(
                2,
                0,
                liHTML("...", true),
                liHTML(pageNo - 1, false, pageNo - 1 === pageNo),
                liHTML(pageNo, false, true),
                liHTML(pageNo + 1, false, pageNo + 1 === pageNo),
                liHTML("...", true),
                liHTML(pageCount, false, pageCount === pageNo)
            );
        }
    }
    $(".pagination").html(arr.join(''));
}

function getCustomModel(modelName, data) {
    var result = null;
    $.ajax({
        url: "/api/custom/" + modelName + "/",
        method: "GET",
        data: data,
        async: false,
        success: function (data) { result = data; },
        error: function (xhr) { console.error(xhr.responseText); }
    });
    return result;
}

function mapToChoices(array) {
    return array.map(item => ({value: item.id,label: item.name}));
}
