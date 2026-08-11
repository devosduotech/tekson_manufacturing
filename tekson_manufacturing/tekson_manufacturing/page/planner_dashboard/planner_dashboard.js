frappe.pages['planner-dashboard'].on_page_load = function(wrapper) {
    let page = frappe.ui.make_app_page({parent: wrapper, title: 'Planner Dashboard', single_column: true});
    
    page.body.html(`
    <div style="padding:20px; max-width:1300px;">
        <div class="row" id="kpi_cards"></div>
        <hr><h5>Production Calendar</h5>
        <div id="calendar_view" style="max-height:300px; overflow-y:auto;"></div>
        <hr><div class="row">
            <div class="col-sm-6"><h5>Department Load</h5><div id="dept_load"></div></div>
            <div class="col-sm-6"><h5>FG Product Mix</h5><div id="fg_mix" style="max-height:250px; overflow-y:auto;"></div></div>
        </div>
        <hr><h5>Exceptions</h5><div id="exceptions"></div>
        <hr><h5>Quick Actions</h5>
        <a href="/app/production-plan" class="btn btn-default btn-sm">Production Plans</a>
        <a href="/app/work-order" class="btn btn-default btn-sm">Work Orders</a>
        <a href="/app/material-planning" class="btn btn-default btn-sm">Material Planning</a>
        <a href="/app/query-report/Work Order Summary" class="btn btn-default btn-sm">WO Report</a>
    </div>`);
    
    // KPIs
    frappe.call({method:'tekson_manufacturing.api.intelligence.planner_kpis',callback:function(r){
        let d=r.message||{};
        page.body.find('#kpi_cards').html(
            '<div class="col-sm-2"><div class="card" style="padding:15px;text-align:center;background:#e3f2fd"><h3>'+(d.total_wo||0)+'</h3><small>Total WOs</small></div></div>'+
            '<div class="col-sm-2"><div class="card" style="padding:15px;text-align:center;background:#e8f5e9"><h3>'+(d.completed_wo||0)+'</h3><small>Completed</small></div></div>'+
            '<div class="col-sm-2"><div class="card" style="padding:15px;text-align:center;background:#fff3e0"><h3>'+(d.in_process_wo||0)+'</h3><small>In Process</small></div></div>'+
            '<div class="col-sm-2"><div class="card" style="padding:15px;text-align:center;background:#fce4ec"><h3>'+(d.pending_pp||0)+'</h3><small>Pending PPs</small></div></div>'+
            '<div class="col-sm-2"><div class="card" style="padding:15px;text-align:center;background:#f3e5f5"><h3>'+(d.on_time_pct||0)+'%</h3><small>On-Time</small></div></div>'
        );
    }});
    
    // Calendar
    frappe.call({method:'tekson_manufacturing.api.intelligence.planner_calendar',callback:function(r){
        let d=r.message||{}, cal=d.calendar||{}, html='<table class="table table-bordered table-sm"><tr><th>Date</th><th>WOs</th><th>Items</th></tr>';
        Object.keys(cal).sort().forEach(function(dt){
            let c=cal[dt]; html+='<tr><td><b>'+dt+'</b></td><td>'+c.count+'</td><td>'+c.items+'</td></tr>';
        });
        html+='</table>'; page.body.find('#calendar_view').html(html);
    }});
    
    // Workload
    frappe.call({method:'tekson_manufacturing.api.intelligence.planner_workload',callback:function(r){
        let d=r.message||{}, dl=d.dept_load||{}, dm=d.fg_mix||{};
        let h='<table class="table table-bordered table-sm"><tr><th>Dept</th><th>WOs</th></tr>';
        Object.entries(dl.dept_count||{}).forEach(function(e){h+='<tr><td>'+e[0]+'</td><td>'+e[1]+'</td></tr>';});
        h+='</table>'; page.body.find('#dept_load').html(h);
        h='<table class="table table-bordered table-sm"><tr><th>FG Item</th><th>Qty</th></tr>';
        Object.entries(dm).slice(0,10).forEach(function(e){h+='<tr><td>'+e[0].substring(0,40)+'</td><td>'+e[1]+'</td></tr>';});
        h+='</table>'; page.body.find('#fg_mix').html(h);
    }});
    
    // Exceptions
    frappe.call({method:'tekson_manufacturing.api.intelligence.planner_exceptions',callback:function(r){
        let d=r.message||{}, html='<div class="row">';
        ['overdue','blocked','material_short','dependency_wait'].forEach(function(k){
            let arr=d[k]||[], color=k==='overdue'?'#ffebee':k==='blocked'?'#fff3e0':k==='material_short'?'#e8eaf6':'#e8f5e9';
            html+='<div class="col-sm-3"><div class="card" style="padding:10px;background:'+color+'"><b>'+k.replace(/_/g,' ').toUpperCase()+'</b><h2>'+arr.length+'</h2>';
            arr.slice(0,3).forEach(function(x){
                html+='<small><a href="/app/work-order/'+(x.wo||'')+'">'+(x.wo||x.name||'')+'</a>: '+(x.op||x.item||x.reason||'')+'</small><br>';
            });
            html+='</div></div>';
        });
        html+='</div>'; page.body.find('#exceptions').html(html);
    }});
};