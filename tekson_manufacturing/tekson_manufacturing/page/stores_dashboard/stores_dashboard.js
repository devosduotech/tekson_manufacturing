frappe.pages['stores-dashboard'].on_page_load = function(wrapper) {
    let page = frappe.ui.make_app_page({parent: wrapper, title: 'Stores Dashboard', single_column: true});
    
    let html = `<div style="padding:20px; max-width:1200px;">
        <div class="row" id="kpi_row">
            <div class="col-sm-3"><div class="card" style="padding:15px; text-align:center; background:#e3f2fd;"><h1 id="kpi_mr">-</h1><small>Today's MRs</small></div></div>
            <div class="col-sm-3"><div class="card" style="padding:15px; text-align:center; background:#fff3e0;"><h1 id="kpi_short">-</h1><small>Items Short</small></div></div>
            <div class="col-sm-3"><div class="card" style="padding:15px; text-align:center; background:#e8f5e9;"><h1 id="kpi_transfer">-</h1><small>Pending Transfers</small></div></div>
            <div class="col-sm-3"><div class="card" style="padding:15px; text-align:center; background:#fce4ec;"><h1 id="kpi_depts">-</h1><small>Departments</small></div></div>
        </div>
        <hr>
        <div class="row">
            <div class="col-sm-4">
                <h5>Quick Actions</h5>
                <a href="/app/material-request" class="btn btn-default btn-block">Material Requests</a>
                <a href="/app/stock-entry/new-stock-entry-3CgGbj6rsu" class="btn btn-default btn-block">New Material Transfer</a>
                <a href="/app/material-planning" class="btn btn-default btn-block">Daily Material Planning</a>
            </div>
            <div class="col-sm-8">
                <h5>Department Shortage Breakdown</h5>
                <div id="dept_breakdown"></div>
            </div>
        </div>
    </div>`;
    page.body.html(html);
    
    frappe.call({
        method: 'tekson_manufacturing.api.intelligence.stores_kpis',
        callback: function(r) {
            let d = r.message || {};
            page.body.find('#kpi_mr').text(d.mr_count || 0);
            page.body.find('#kpi_short').text(d.items_short || 0);
            page.body.find('#kpi_transfer').text(d.mr_count || 0);
            page.body.find('#kpi_depts').text(Object.keys(d.dept_breakdown || {}).length);
            
            let html = '<table class="table table-bordered"><tr><th>Department</th><th>Items Short</th></tr>';
            Object.entries(d.dept_breakdown || {}).forEach(function(e) {
                html += '<tr><td>' + e[0] + '</td><td>' + e[1] + '</td></tr>';
            });
            html += '</table>';
            page.body.find('#dept_breakdown').html(html);
        }
    });
};