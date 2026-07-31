#import frappe

#from tekson_manufacturing.manufacturing.work_order import complete_work_order


#def after_submit(doc, method=None):

#    if not doc.work_order:
#        return

#    frappe.enqueue_after_commit(
#        complete_work_order,
#        work_order=doc.work_order,
#    )

import frappe

from tekson_manufacturing.manufacturing.work_order import complete_work_order


def after_submit(doc, method=None):

    if not doc.work_order:
        return

    frappe.enqueue(
        "tekson_manufacturing.manufacturing.work_order.complete_work_order",
        queue="short",
        enqueue_after_commit=True,
        work_order=doc.work_order,
    )
