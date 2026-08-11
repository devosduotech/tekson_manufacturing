frappe.pages['planner-dashboard'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Planner Dashboard',
        single_column: true
    });

    // Build HTML structure
    $(wrapper).on('show', function() {
        $(wrapper).html(`
            <div style="padding:20px; max-width:1400px;">
                <!-- Date Range -->
                <div class="row" style="margin-bottom:20px;">
                    <div class="col-sm-4">
                        <label><b>Planned Date:</b></label>
                        <input id="plan_date" type="date" class="form-control" value="${frappe.datetime.get_today()}">
                    </div>
                    <div class="col-sm-2" style="padding-top:25px;">
                        <button id="refresh_btn" class="btn btn-primary btn-sm">Refresh</button>
                    </div>
                    <div class="col-sm-2" style="padding-top:25px;">
                        <button id="today_btn" class="btn btn-default btn-sm">Today</button>
                    </div>
                </div>

                <!-- KPI Cards -->
                <div class="row" id="kpi_cards" style="margin-bottom:20px;"></div>

                <hr>

                <!-- Production Calendar -->
                <h5><i class="fa fa-calendar"></i> Production Calendar</h5>
                <div id="calendar" style="max-height:300px; overflow-y:auto; margin-bottom:20px;"></div>

                <hr>

                <!-- Department Load & FG Mix -->
                <div class="row" style="margin-bottom:20px;">
                    <div class="col-sm-6">
                        <h5><i class="fa fa-industry"></i> Department Load</h5>
                        <div id="dept_load"></div>
                    </div>
                    <div class="col-sm-6">
                        <h5><i class="fa fa-cubes"></i> FG Product Mix</h5>
                        <div id="fg_mix" style="max-height:250px; overflow-y:auto;"></div>
                    </div>
                </div>

                <hr>

                <!-- Exceptions -->
                <h5><i class="fa fa-exclamation-triangle"></i> Exceptions</h5>
                <div id="exceptions" style="margin-bottom:20px;"></div>

                <hr>

                <!-- Quick Actions -->
                <h5>Quick Actions</h5>
                <a href="/app/production-plan" class="btn btn-default btn-sm">Production Plans</a>
                <a href="/app/work-order" class="btn btn-default btn-sm">Work Orders</a>
                <a href="/app/material-planning" class="btn btn-default btn-sm">Material Planning</a>
            </div>
        `);

        // Today button handler
        $('#today_btn').on('click', function() {
            $('#plan_date').val(frappe.datetime.get_today());
            load_dashboard();
        });

        // Refresh button handler
        $('#refresh_btn').on('click', load_dashboard);

        // Initial load
        load_dashboard();
    });

    function load_dashboard() {
        var planned_date = $('#plan_date').val();

        // Load KPIs
        frappe.call({
            method: 'tekson_manufacturing.api.intelligence.planner_kpis',
            args: { planned_date: planned_date },
            callback: function(r) {
                if (!r.message) return;
                var d = r.message;
                $('#kpi_cards').html(`
                    <div class="col-sm-2">
                        <div class="card" style="padding:15px; text-align:center; background:#e3f2fd">
                            <h3>${d.total_wo || 0}</h3>
                            <small>Total WOs</small>
                        </div>
                    </div>
                    <div class="col-sm-2">
                        <div class="card" style="padding:15px; text-align:center; background:#e8f5e9">
                            <h3>${d.completed_wo || 0}</h3>
                            <small>Completed</small>
                        </div>
                    </div>
                    <div class="col-sm-2">
                        <div class="card" style="padding:15px; text-align:center; background:#fff3e0">
                            <h3>${d.in_process_wo || 0}</h3>
                            <small>In Process</small>
                        </div>
                    </div>
                    <div class="col-sm-2">
                        <div class="card" style="padding:15px; text-align:center; background:#c8e6c9">
                            <h3>${d.readiness_pct || 0}%</h3>
                            <small>Readiness</small>
                        </div>
                    </div>
                    <div class="col-sm-2">
                        <div class="card" style="padding:15px; text-align:center; background:#f3e5f5">
                            <h3>${d.on_time_pct || 0}%</h3>
                            <small>On-Time</small>
                        </div>
                    </div>
                    <div class="col-sm-2">
                        <div class="card" style="padding:15px; text-align:center; background:#fce4ec">
                            <h3>${d.pending_pp || 0}</h3>
                            <small>Pending PPs</small>
                        </div>
                    </div>
                `);
            }
        });

        // Load Calendar
        frappe.call({
            method: 'tekson_manufacturing.api.intelligence.planner_calendar',
            args: { from_date: planned_date, days: 7 },
            callback: function(r) {
                if (!r.message || !r.message.calendar) return;
                var cal = r.message.calendar;
                var html = '<table class="table table-bordered table-sm"><tr><th>Date</th><th>WOs</th><th>Qty</th><th>Items</th></tr>';
                Object.keys(cal).sort().forEach(function(dt) {
                    var c = cal[dt];
                    var items = c.wos.map(function(w) { return w.item; }).slice(0, 3).join(', ');
                    html += '<tr><td><b>' + dt + '</b></td><td>' + c.count + '</td><td>' + c.items + '</td><td><small>' + items + '</small></td></tr>';
                });
                html += '</table>';
                $('#calendar').html(html);
            }
        });

        // Load Workload
        frappe.call({
            method: 'tekson_manufacturing.api.intelligence.planner_workload',
            args: { planned_date: planned_date },
            callback: function(r) {
                if (!r.message) return;
                var dl = r.message.dept_load || {};
                var fm = r.message.fg_mix || {};

                // Department Load
                var dl_html = '<table class="table table-bordered table-sm"><tr><th>Department</th><th>WOs</th></tr>';
                Object.entries(dl.dept_count || {}).forEach(function(e) {
                    dl_html += '<tr><td>' + e[0] + '</td><td>' + e[1] + '</td></tr>';
                });
                dl_html += '</table>';
                $('#dept_load').html(dl_html);

                // FG Mix
                var fm_html = '<table class="table table-bordered table-sm"><tr><th>FG Item</th><th>Qty</th></tr>';
                Object.entries(fm).slice(0, 10).forEach(function(e) {
                    fm_html += '<tr><td>' + e[0].substring(0, 40) + '</td><td>' + e[1] + '</td></tr>';
                });
                fm_html += '</table>';
                $('#fg_mix').html(fm_html);
            }
        });

        // Load Exceptions
        frappe.call({
            method: 'tekson_manufacturing.api.intelligence.planner_exceptions',
            args: { planned_date: planned_date },
            callback: function(r) {
                if (!r.message) return;
                var d = r.message;
                var sev = d.severity || {};
                var html = '<div class="row">';

                // Severity badges
                html += '<div class="col-sm-12" style="margin-bottom:10px;">';
                if (sev.critical) html += '<span class="badge" style="background:red; margin-right:5px;">' + sev.critical + ' Critical</span> ';
                if (sev.high) html += '<span class="badge" style="background:orange; margin-right:5px;">' + sev.high + ' High</span> ';
                if (sev.medium) html += '<span class="badge" style="background:#ffc107; margin-right:5px;">' + sev.medium + ' Medium</span> ';
                html += '</div>';

                // Overdue
                html += '<div class="col-sm-3"><div class="card" style="padding:10px; background:#ffebee"><b>Overdue</b><h2>' + (d.summary.overdue || 0) + '</h2>';
                (d.overdue || []).slice(0, 3).forEach(function(x) {
                    html += '<small><a href="/app/work-order/' + x.name + '">' + x.name + '</a>: ' + x.days_overdue + 'd</small><br>';
                });
                html += '</div></div>';

                // Blocked
                html += '<div class="col-sm-3"><div class="card" style="padding:10px; background:#fff3e0"><b>Blocked</b><h2>' + (d.summary.blocked || 0) + '</h2>';
                (d.blocked || []).slice(0, 3).forEach(function(x) {
                    html += '<small><a href="/app/job-card/' + x.name + '">' + x.wo + '</a>: ' + x.reason + '</small><br>';
                });
                html += '</div></div>';

                // Material Short
                html += '<div class="col-sm-3"><div class="card" style="padding:10px; background:#e8eaf6"><b>Material Short</b><h2>' + (d.summary.material_short || 0) + '</h2>';
                (d.material_short || []).slice(0, 3).forEach(function(x) {
                    html += '<small><a href="/app/job-card/' + x.name + '">' + x.wo + '</a>: ' + x.op + '</small><br>';
                });
                html += '</div></div>';

                // Dependency Wait
                html += '<div class="col-sm-3"><div class="card" style="padding:10px; background:#e8f5e9"><b>Dependency Wait</b><h2>' + (d.summary.dependency_wait || 0) + '</h2>';
                (d.dependency_wait || []).slice(0, 3).forEach(function(x) {
                    html += '<small><a href="/app/job-card/' + x.name + '">' + x.wo + '</a>: ' + x.op + '</small><br>';
                });
                html += '</div></div></div>';

                $('#exceptions').html(html);
            }
        });
    }
};
