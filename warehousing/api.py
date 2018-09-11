from __future__ import unicode_literals
import frappe
from frappe.utils import cint, get_gravatar, format_datetime, now_datetime,add_days,today,formatdate,date_diff,getdate,get_last_day
from frappe import throw, msgprint, _
from frappe.utils.password import update_password as _update_password
from frappe.desk.notifications import clear_notifications
from frappe.utils.user import get_system_managers
import frappe.permissions
import frappe.share
import re
import string
import random
import json
import time
from datetime import datetime
from datetime import date
from datetime import timedelta
import collections
import math
import logging


@frappe.whitelist()
def customerPermission(doc,method):
	if doc.sales_person:
		addUserPermission(doc.name,doc.sales_person)
	else:
		removeUserPermission(doc.name)



@frappe.whitelist()
def getLastPackageNumber(customer):
	last_no=frappe.db.sql("""select package_no from `tabPacking Slips` where customer=%s  order by  creation desc limit 1""",customer)
	if last_no:
		return int(last_no[0][0])+1
	else:
		return 1
	
	
	




@frappe.whitelist()
def addUserPermission(allow_val,employee):
	d=frappe.get_doc({
				 	"docstatus": 0,
				 	"doctype": "User Permission",
				 	"name": "New User Permission 1",
				 	"__islocal": 1,
				 	"__unsaved": 1,
				 	"owner": "Administrator",
				 	"apply_for_all_roles": 0,
				 	"user": getUserIdFromEmployeeId(employee),
				 	"allow":"Customer",
				 	"for_value": str(allow_val)
				 })
	d.insert(ignore_permissions=True)

@frappe.whitelist()
def removeUserPermission(customer):
	frappe.db.sql("""delete from `tabUser Permission` where allow='Customer' and for_value=%s""",customer)
	
	


@frappe.whitelist()
def getUserIdFromEmployeeId(emp_code):
	userid=frappe.db.sql("""select user_id from `tabEmployee` where name=%s""",emp_code)
	if userid:
		return userid[0][0]


@frappe.whitelist()
def addCustomerInGL(doc,method):
	glentries=frappe.db.sql("""select name,party from `tabGL Entry` where voucher_no='"""+doc.name+"""'""")
	if glentries:
		for gl in glentries:
			frappe.msgprint(str(gl[0]))
			if doc.doctype=="Sales Invoice":
				updateGL(gl[0],doc.customer)
			if doc.doctype=="Payment Entry":
				updateGL(gl[0],doc.party)
			if doc.doctype=="Journal Entry":
				updateGL(gl[0],gl[1])






@frappe.whitelist()
def updateGL(name,party):
	frappe.db.commit()
	#frappe.client.set_value("GL Entry",name,"customer",str(party))
	if not party==None:
		frappe.msgprint(str(party))
		frappe.db.sql("""update `tabGL Entry` set customer='"""+str(party)+"""' where name='"""+str(name)+"""'""")
		frappe.db.commit()


@frappe.whitelist()
def assignSalesOrderInDelivery(delivery_id):
	doc=frappe.get_doc("Delivery Note",delivery_id)
	sales_order_list=frappe.db.sql("""select name from `tabSales Order` where customer=%s and status in('To Deliver','To Deliver and Bill')""",doc.customer)
	#return sales_order_list
	for row in sales_order_list:
		sales_order_data=frappe.get_doc("Sales Order",row[0])
		#return row[0]
		for delivery_item in doc.items:
			for order_item in sales_order_data.items:
				check_item=frappe.get_doc("Delivery Note Item",delivery_item.name)
				if check_item.against_sales_order==None:
					if order_item.item_code==delivery_item.item_code:
						if int(order_item.qty)>=int(delivery_item.qty):
							frappe.db.sql("""update `tabSales Order Item` set delivered_qty=%s where name=%s""",(delivery_item.qty,order_item.name))
							delivery_update=frappe.get_doc("Delivery Note Item",delivery_item.name)
							delivery_update.against_sales_order=row[0]
							delivery_update.save()
						else:
							frappe.db.sql("""update `tabSales Order Item` set delivered_qty=%s where name=%s""",(order_item.qty,order_item.name))	
							qty_diff=int(delivery_item.qty)-int(order_item.qty)
							delivery_update=frappe.get_doc("Delivery Note Item",delivery_item.name)
							delivery_update.against_sales_order=row[0]
							so_detail=order_item.name
							delivery_update.save()
							data_del=frappe.get_doc("Delivery Note",delivery_item.parent)
							idx_len=len(data_del.items)+1
							#deli_item=frappe.get_doc({
						#			"doctype":"Delivery Note Item",
						#			"name":"New Delivery Note Item 1",
						#			"item_code":str(delivery_item.item_code),
						#			"qty":str(qty_diff),
						#			"parent":str(doc.name),
						#			"parenttype": "Delivery Note",
						#			"parentfield": "items",
						#			"uom":str(delivery_item.uom),
						#			"item_name":str(delivery_item.item_name),
						#			"rate":str(delivery_item.rate),
						#			"conversion_factor":delivery_item.conversion_factor,
						#			"idx":idx_len
						#			})
						
						#deli_item.insert()
		doc_final=frappe.get_doc("Delivery Note",delivery_id)
		doc_final.submit()



@frappe.whitelist()
def assignSalesOrderInDelivery1(delivery_id):
	doc=frappe.get_doc("Delivery Note",delivery_id)
	sales_order_list=frappe.db.sql("""select name from `tabSales Order` where customer=%s and status in('To Deliver','To Deliver and Bill')""",doc.customer)
	#return sales_order_list
	#return sales_order_list
	for row in sales_order_list:
		sales_order_data=frappe.get_doc("Sales Order",row[0])
		#return row[0]
		for order_item in sales_order_data.items:
			doc_delivery=frappe.get_doc("Delivery Note",delivery_id)
			for delivery_item in doc_delivery.items:
				check_item=frappe.get_doc("Delivery Note Item",delivery_item.name)
				if check_item.against_sales_order==None:
					if order_item.item_code==delivery_item.item_code:
						if int(order_item.qty)>=int(delivery_item.qty):
							if int(order_item.qty)==int(order_item.delivered_qty):
								continue
							else:

								frappe.db.sql("""update `tabSales Order Item` set delivered_qty=%s where name=%s""",(delivery_item.qty,order_item.name))
								#delivery_update=frappe.get_doc("Delivery Note Item",delivery_item.name)
								#delivery_update.against_sales_order=row[0]
								#delivery_update.save()
								frappe.db.sql("""update `tabDelivery Note Item` set against_sales_order=%s,so_detail=%s where name=%s""",(order_item.parent,order_item.name,delivery_item.name))
								del_doc_change=frappe.get_doc("Delivery Note",delivery_item.parent)
								del_doc_change.save()
						else:
							if int(order_item.qty)==int(order_item.delivered_qty):
								continue
							else:
								del_qty=int(order_item.qty)-int(order_item.delivered_qty)
								frappe.db.sql("""update `tabSales Order Item` set delivered_qty=%s where name=%s""",(del_qty,order_item.name))	
								qty_diff=int(delivery_item.qty)-int(del_qty)
								#delivery_update=frappe.get_doc("Delivery Note Item",delivery_item.name)
								frappe.db.sql("""update `tabDelivery Note Item` set against_sales_order=%s,so_detail=%s where name=%s""",(order_item.parent,order_item.name,delivery_item.name))
								#delivery_update.against_sales_order=row[0]
								#so_detail=order_item.name
								#delivery_update.save()
								data_del=frappe.get_doc("Delivery Note",delivery_item.parent)
								idx_len=len(data_del.items)+1
								update_del_item=frappe.get_doc("Delivery Note Item",delivery_item.name)
								update_del_item.qty=del_qty
								update_del_item.save()
								deli_item=frappe.get_doc({
										"doctype":"Delivery Note Item",
										"name":"New Delivery Note Item 1",
										"item_code":str(delivery_item.item_code),
										"qty":str(qty_diff),
										"parent":str(doc.name),
										"parenttype": "Delivery Note",
										"parentfield": "items",
										"uom":str(delivery_item.uom),
										"item_name":str(delivery_item.item_name),
										"rate":str(delivery_item.rate),
										"conversion_factor":delivery_item.conversion_factor,
										"idx":idx_len,
										"warehouse":delivery_item.warehouse,
										"cost_center":delivery_item.cost_center
										})
						
								deli_item.insert()
								del_doc_change=frappe.get_doc("Delivery Note",delivery_item.parent)
								del_doc_change.save()
		doc_final=frappe.get_doc("Delivery Note",delivery_id)
		doc_final.save()
		
	
	



	

	
	
