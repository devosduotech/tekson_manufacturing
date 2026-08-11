frappe.pages['planner-dashboard'].on_page_load = function(wrapper) {
    let page = frappe.ui.make_app_page({parent: wrapper, title: 'Planner Dashboard', single_column: true});
    
    let html = `<div style="padding:20px; max-width:1200px;">
        <div class="row" id="kpi_row">
            <div class="col-sm-3"><div class="card" style="padding:15px; text-align:center; background:#e3f2fd;"><h1 id="kpi_total">-</h1><small>Total Work Orders</small></div></div>
            <div class="col-sm-3"><div class="card" style="padding:15px; text-align:center; background:#e8f5e9;"><h1 id="kpi_complete">-</h1><small>Completed</small></div></div>
            <div class="col-sm-3"><div class="card" style="padding:15px; text-align:center; background:#fff3e0;"><h1 id="kpi_inprog">-</h1><small>In Process</small></div></div>
            <div class="col-sm-3"><div class="card" style="padding:15px; text-align:center; background:#fce4ec;"><h1 id="kpi_otd">-</h1><small>On-Time %</small></div></div>
        </div>
        <hr>
        <div class="row">
            <div class="col-sm-4">
                <h5>Quick Actions</h5>
                <a href="/app/production-plan" class="btn btn-default btn-block">Production Plans</a>
                <a href="/app/work-order" class="btn btn-default btn-block">Work Orders</a>
                <a href="/app/material-planning" class="btn btn-default btn-block">Daily Material Planning</a>
            </div>
            <div class="col-sm-8">
                <h5>Department Status</h5>
                <div id="dept_status"></div>
            </div>
        </div>
    </div>`;
    page.body.html(html);
    
    frappe.call({
        method: 'tekson_manufacturing.api.intelligence.planner_kpis',
        callback: function(r) {
            let d = r.message || {};
            page.body.find('#kpi_total').text(d.total_wo || 0);
            page.body.find('#kpi_complete').text(d.completed_wo || 0);
            page.body.find('#kpi_inprog').text(d.in_process_wo || 0);
            page.body.find('#kpi_otd').text((d.on_time_pct || 0) + '%');
            
            let dept_html = '<table class="table table-bordered"><tr><th>Metric</th><th>Value</th></tr>';
            dept_html += '<tr><td>Pending PPs</td><td>' + (d.pending_pp || 0) + '</td></tr>';
            dept_html += '<tr><td>Planned vs Actual</td><td>' + (d.planned_vs_actual?.completed || 0) + ' / ' + (d.planned_vs_actual?.planned || 0) + '</td></tr>';
            dept_html += '</table>';
            page.body.find('#dept_status').html(dept_html);
        }
    });
};