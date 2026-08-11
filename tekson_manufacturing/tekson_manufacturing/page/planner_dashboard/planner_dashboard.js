frappe.pages['planner-dashboard'].on_page_load = function(wrapper) {
    let page = frappe.ui.make_app_page({parent: wrapper, title: 'Planner Dashboard', single_column: true});
    
    page.body.html(`
    <div style="padding:20px; max-width:1300px;">
        <div class="row" style="margin-bottom:15px;">
            <div class="col-sm-4">
                <label><b>Date Range:</b></label>
                <div class="row">
                    <div class="col-sm-5"><input id="from_date" type="date" class="form-control"></div>
                    <div class="col-sm-2" style="text-align:center; padding-top:7px;">to</div>
                    <div class="col-sm-5"><input id="to_date" type="date" class="form-control"></div>
                </div>
            </div>
            <div class="col-sm-2" style="padding-top:25px;"><button id="refresh_btn" class="btn btn-primary btn-sm">Refresh</button></div>
            <div class="col-sm-2" style="padding-top:25px;"><button id="today_btn" class="btn btn-default btn-sm">Today</button></div>
        </div>
        <div class="row" id="kpi_cards"></div>
        <hr><h5>FG Items In Process (Today)</h5><div id="fg_today" style="margin-bottom:15px;"></div>
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
    </div>`);
    
    // Set default dates
    document.getElementById('from_date').value = frappe.datetime.get_today();
    document.getElementById('to_date').value = frappe.datetime.get_today();
    
    document.getElementById('today_btn').addEventListener('click', function(){
        document.getElementById('from_date').value = frappe.datetime.get_today();
        document.getElementById('to_date').value = frappe.datetime.get_today();
        loadAll();
    });
    
    function loadAll(){
        page.body.find('#refresh_btn').prop('disabled',true).text('Loading...');
        var from_date = document.getElementById('from_date').value;
        var to_date = document.getElementById('to_date').value;
        
        // KPIs — use from_date
        frappe.call({method:'tekson_manufacturing.api.intelligence.planner_kpis',args:{planned_date:from_date},callback:function(r){
            let d=r.message||{};
            page.body.find('#kpi_cards').html(
                '<div class="col-sm-2"><div class="card" style="padding:15px;text-align:center;background:#e3f2fd"><h3>'+(d.total_wo||0)+'</h3><small>Total WOs<br>'+from_date+'</small></div></div>'+
                '<div class="col-sm-2"><div class="card" style="padding:15px;text-align:center;background:#e8f5e9"><h3>'+(d.completed_wo||0)+'</h3><small>Completed</small></div></div>'+
                '<div class="col-sm-2"><div class="card" style="padding:15px;text-align:center;background:#fff3e0"><h3>'+(d.in_process_wo||0)+'</h3><small>In Process</small></div></div>'+
                '<div class="col-sm-2"><div class="card" style="padding:15px;text-align:center;background:#c8e6c9"><h3>'+(d.readiness_pct||0)+'%</h3><small>Readiness</small></div></div>'+
                '<div class="col-sm-2"><div class="card" style="padding:15px;text-align:center;background:#f3e5f5"><h3>'+(d.on_time_pct||0)+'%</h3><small>On-Time</small></div></div>'+
                '<div class="col-sm-2"><div class="card" style="padding:15px;text-align:center;background:#fce4ec"><h3>'+(d.pending_pp||0)+'</h3><small>Pending PPs</small></div></div>'
            );
        }});
        
        // Calendar — date range
        frappe.call({method:'tekson_manufacturing.api.intelligence.planner_calendar',args:{from_date:from_date,to_date:to_date},callback:function(r){
            let d=r.message||{}, cal=d.calendar||{}, html='<table class="table table-bordered table-sm"><tr><th>Date</th><th>WOs</th><th>FG Items</th></tr>';
            Object.keys(cal).sort().forEach(function(dt){if(dt>=from_date && dt<=to_date){let c=cal[dt];html+='<tr><td><b>'+dt+'</b></td><td>'+c.count+'</td><td>'+c.items+'</td></tr>';}});
            html+='</table>'; page.body.find('#calendar_view').html(html);
        }});
        
        // Workload — use from_date
        frappe.call({method:'tekson_manufacturing.api.intelligence.planner_workload',args:{planned_date:from_date},callback:function(r){
            let d=r.message||{}, dl=d.dept_load||{}, dm=d.fg_mix||{};
            let h='<table class="table table-bordered table-sm"><tr><th>Dept</th><th>WOs</th></tr>';
            Object.entries(dl.dept_count||{}).forEach(function(e){h+='<tr><td>'+e[0]+'</td><td>'+e[1]+'</td></tr>';});
            h+='</table>'; page.body.find('#dept_load').html(h);
            h='<table class="table table-bordered table-sm"><tr><th>FG Item</th><th>Qty</th></tr>';
            Object.entries(dm).slice(0,10).forEach(function(e){h+='<tr><td>'+e[0].substring(0,40)+'</td><td>'+e[1]+'</td></tr>';});
            h+='</table>'; page.body.find('#fg_mix').html(h);
        }});
        
        // Exceptions — use from_date
        frappe.call({method:'tekson_manufacturing.api.intelligence.planner_exceptions',args:{planned_date:from_date},callback:function(r){
            let d=r.message||{}, s=d.summary||{}, sev=d.severity||{};
            let html='<div class="row"><div class="col-sm-12" style="margin-bottom:10px"><b>Overdue:</b> ';
            if(sev.critical) html+='<span class="badge" style="background:red">'+sev.critical+' Critical</span> ';
            if(sev.high) html+='<span class="badge" style="background:orange">'+sev.high+' High</span> ';
            if(sev.medium) html+='<span class="badge" style="background:#ffc107">'+sev.medium+' Medium</span> ';
            html+='</div>';
            html+='<div class="col-sm-3"><div class="card" style="padding:10px;background:#ffebee"><b>Overdue</b><h2>'+s.overdue+'</h2>';
            (d.overdue||[]).slice(0,3).forEach(function(x){html+='<small><a href="/app/work-order/'+x.name+'">'+x.name+'</a>: '+x.days_overdue+'d</small><br>';});
            html+='</div></div>';
            html+='<div class="col-sm-3"><div class="card" style="padding:10px;background:#fff3e0"><b>Blocked</b><h2>'+s.blocked+'</h2>';
            (d.blocked||[]).slice(0,3).forEach(function(x){html+='<small><a href="/app/work-order/'+x.wo+'">'+x.wo+'</a>: '+x.reason+'</small><br>';});
            html+='</div></div>';
            html+='<div class="col-sm-3"><div class="card" style="padding:10px;background:#e8eaf6"><b>Material Short</b><h2>'+s.material_short+'</h2>';
            (d.material_short||[]).slice(0,3).forEach(function(x){html+='<small><a href="/app/work-order/'+x.wo+'">'+x.wo+'</a>: '+x.op+'</small><br>';});
            html+='</div></div>';
            html+='<div class="col-sm-3"><div class="card" style="padding:10px;background:#e8f5e9"><b>Dependency Wait</b><h2>'+s.dependency_wait+'</h2>';
            (d.dependency_wait||[]).slice(0,3).forEach(function(x){html+='<small><a href="/app/work-order/'+x.wo+'">'+x.wo+'</a>: '+x.op+'</small><br>';});
            html+='</div></div></div>';
            page.body.find('#exceptions').html(html);
        }});
        
        // FG Today In Process — from Production Plan Item (submitted PPs)
        frappe.call({method:'frappe.client.get_list',args:{doctype:'Production Plan Item',
            fields:['item_code','item_name','planned_qty','parent'],filters:{docstatus:1},
            start:0,page_length:50},callback:function(r){
            let items=r.message||[];
            // Group by item_code
            let grouped={};
            items.forEach(function(it){
                if(!grouped[it.item_code]) grouped[it.item_code]={qty:0,wo_count:0,name:it.item_name||it.item_code};
                grouped[it.item_code].qty+=parseFloat(it.planned_qty||0);
            });
            // Get WO count per item
            let item_list=Object.keys(grouped);
            if(item_list.length>0){
                frappe.call({method:'frappe.client.get_list',args:{doctype:'Work Order',
                    fields:['production_item','name'],filters:{production_item:['in',item_list],docstatus:1,status:['in',['In Process','Completed']]},
                    start:0,page_length:500},callback:function(r2){
                    let wos=r2.message||[];
                    wos.forEach(function(w){
                        if(grouped[w.production_item]) grouped[w.production_item].wo_count++;
                    });
                    let html='<table class="table table-bordered table-sm"><tr><th>FG Item</th><th>Name</th><th>Planned Qty</th><th>WO Count</th></tr>';
                    Object.entries(grouped).forEach(function(e){
                        let code=e[0], d=e[1];
                        html+='<tr><td><b>'+code+'</b></td><td>'+(d.name||'')+'</td><td>'+d.qty+'</td><td>'+d.wo_count+'</td></tr>';
                    });
                    html+='</table>';
                    page.body.find('#fg_today').html(html);
                }});
            } else {
                page.body.find('#fg_today').html('<p class="text-muted">No FG items in Production Plans</p>');
            }
        }});
        
        page.body.find('#refresh_btn').prop('disabled',false).text('Refresh');
    }
    
    page.body.find('#refresh_btn').on('click',loadAll);
    loadAll();
};