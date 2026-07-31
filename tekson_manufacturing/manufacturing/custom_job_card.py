import frappe

from erpnext.manufacturing.doctype.job_card.job_card import JobCard
from tekson_manufacturing.manufacturing.work_order import complete_work_order


class TeksonJobCard(JobCard):

    def on_submit(self):

        super().on_submit()

        if not self.work_order:
            return

        work_order = self.work_order

        frappe.db.after_commit.add(
            lambda: complete_work_order(work_order)
        )
