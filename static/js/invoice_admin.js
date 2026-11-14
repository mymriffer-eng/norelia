(function () {
    'use strict';

    // Admin URL of the invoice section, e.g. /admin/invoices/invoice/
    var base = window.location.pathname.replace(/invoice\/.*$/, 'invoice/');
    var lookupUrl = base + 'lookup-item/';

    document.addEventListener('change', function (event) {
        var input = event.target;
        var match = input && input.name && input.name.match(/^(items-\d+)-product_sku$/);
        if (!match) {
            return;
        }

        var prefix = match[1];
        var code = input.value.trim();
        if (!code) {
            return;
        }

        fetch(lookupUrl + '?code=' + encodeURIComponent(code), {
            credentials: 'same-origin',
            headers: {'X-Requested-With': 'XMLHttpRequest'}
        })
            .then(function (response) { return response.json(); })
            .then(function (data) {
                if (!data.found) {
                    return;
                }
                var nameInput = document.getElementById('id_' + prefix + '-product_name');
                var priceInput = document.getElementById('id_' + prefix + '-price');
                if (nameInput) {
                    nameInput.value = data.name;
                }
                if (priceInput) {
                    priceInput.value = data.price;
                }
            });
    });
})();
