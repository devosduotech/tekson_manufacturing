frappe.pages['material-planning'].on_page_load = function(wrapper) {
    let page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Daily Material Planning',
        single_column: true
    });
    
    let body = $(frappe.render_template('daily_material_planning', {}));
    page.body.append(body);
    
    // Load PPs
    frappe.call({
        method: 'tekson_manufacturing.www.mes.daily_material_planning.search_production_plans',
        args: {txt: ''},
        callback: function(r) {
            let select = body.find('#production_plan');
            (r.message || []).forEach(function(pp) {
                select.append('<option value="' + pp.name + '">' + pp.name + '</option>');
            });
        }
    });
    
    body.find('#planned_date').val(frappe.datetime.get_today());
    
    body.find('#generate_btn').on('click', function() {
        let pp = body.find('#production_plan').val();
        let date = body.find('#planned_date').val();
        if (!pp) { frappe.msgprint('Select a Production Plan'); return; }
        
        let btn = $(this);
        btn.prop('disabled', true).text('Generating...');
        
        frappe.call({
            method: 'tekson_manufacturing.planning.material_planning_service.generate_daily_material_requests',
            args: { production_plan: pp, planned_date: date },
            callback: function(r) {
                btn.prop('disabled', false).text('Generate MRs');
                let res = r.message || {};
                let result = body.find('#result').empty();
                
                if (res.created_mrs && res.created_mrs.length > 0) {
                    result.append('<div class="alert alert-success"><b>' + res.created_mrs.length + '</b> MR(s) for <b>' + res.planned_date + '</b></div>');
                    (res.details || []).forEach(function(d) {
                        result.append('<div class="alert alert-info" style="margin:3px 0"><a href="/app/material-request/' + d.name + '"><b>' + d.name + '</b></a> — ' + d.department_wip + ' (' + d.items + ' items)</div>');
                    });
                } else {
                    result.append('<div class="alert alert-warning">' + (res.message || 'All materials in WIP') + '</div>');
                }
            }
        });
    });
};
