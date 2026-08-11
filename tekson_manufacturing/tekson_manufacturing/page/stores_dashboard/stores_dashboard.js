frappe.pages['stores-dashboard'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Stores Dashboard',
        single_column: true
    });

    $(wrapper).on('show', function() {
        $(wrapper).html(`
            <div style="padding:20px; max-width:1400px;">
                <h3>Stores Dashboard - Under Development</h3>
                <p>This dashboard will show material health, pick lists, and WIP transfers.</p>
                <div id="kpi_area"></div>
            </div>
        `);

        // Load basic KPIs
        frappe.call({
            method: 'tekson_manufacturing.api.intelligence.stores_kpis',
            callback: function(r) {
                if (!r.message) return;
                var d = r.message;
                $('#kpi_area').html(`
                    <div class="row">
                        <div class="col-sm-3">
                            <div class="card" style="padding:15px; text-align:center; background:#fff3e0">
                                <h3>${d.pending_mrs || 0}</h3>
                                <small>Pending MRs</small>
                            </div>
                        </div>
                        <div class="col-sm-3">
                            <div class="card" style="padding:15px; text-align:center; background:#e3f2fd">
                                <h3>${d.pending_pick_lists || 0}</h3>
                                <small>Pick Lists</small>
                            </div>
                        </div>
                        <div class="col-sm-3">
                            <div class="card" style="padding:15px; text-align:center; background:#e8f5e9">
                                <h3>${d.wip_transfers || 0}</h3>
                                <small>WIP Transfers</small>
                            </div>
                        </div>
                        <div class="col-sm-3">
                            <div class="card" style="padding:15px; text-align:center; background:#ffebee">
                                <h3>${d.material_short || 0}</h3>
                                <small>Material Short</small>
                            </div>
                        </div>
                    </div>
                `);
            }
        });
    });
};
