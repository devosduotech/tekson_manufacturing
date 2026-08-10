frappe.pages['material-planning'].on_page_load = function(wrapper) {
    let page = frappe.ui.make_app_page({parent: wrapper, title: 'Daily Material Planning', single_column: true});
    
    let html = '<div style="padding:30px; max-width:800px;"><h3>Daily Material Planning</h3><p>Generate Material Requests for stores.</p><hr><div class="row"><div class="col-sm-6"><label>Production Plan</label><select id="pp_select" class="form-control"></select></div><div class="col-sm-3"><label>Planned Start Date</label><input type="date" id="plan_date" class="form-control"></div><div class="col-sm-3"><br><button id="gen_btn" class="btn btn-primary">Generate MRs</button></div></div><div id="result_area" style="margin-top:20px;"></div></div>';
    page.body.html(html);
    
    frappe.call({method:'tekson_manufacturing.www.mes.daily_material_planning.search_production_plans',args:{txt:''},callback:function(r){
        var sel = page.body.find('#pp_select');
        (r.message||[]).forEach(function(pp){sel.append('<option value="'+pp.name+'">'+pp.name+'</option>');});
    }});
    
    page.body.find('#plan_date').val(frappe.datetime.get_today());
    
    page.body.find('#gen_btn').on('click',function(){
        var pp = page.body.find('#pp_select').val(), dt = page.body.find('#plan_date').val();
        if(!pp){frappe.msgprint('Select a Production Plan');return;}
        var btn = page.body.find('#gen_btn');btn.prop('disabled',true).text('Generating...');
        frappe.call({method:'tekson_manufacturing.planning.material_planning_service.generate_daily_material_requests',args:{production_plan:pp,planned_date:dt},callback:function(r){
            btn.prop('disabled',false).text('Generate MRs');
            var res = r.message||{}, area = page.body.find('#result_area').empty();
            if(res.created_mrs && res.created_mrs.length > 0){
                area.append('<div class="alert alert-success"><b>'+res.created_mrs.length+'</b> MR(s) for <b>'+res.planned_date+'</b></div>');
                (res.details||[]).forEach(function(d){area.append('<div class="alert alert-info" style="margin:3px 0"><a href="/app/material-request/'+d.name+'"><b>'+d.name+'</b></a> &mdash; '+d.department_wip+' ('+d.items+' items)</div>');});
            }else{area.append('<div class="alert alert-warning">'+(res.message||'All materials in WIP')+'</div>');}
        }});
    });
};
