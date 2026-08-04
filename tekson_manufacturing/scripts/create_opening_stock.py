"""
Opening Stock Creator for BOM Components

Creates a Material Receipt Stock Entry to add opening stock for all raw materials
used in BOMs.

Usage:
    # Create opening stock for all BOM components
    bench --site teksons.dev execute tekson_manufacturing.scripts.create_opening_stock.create_opening_stock --args '["Stores - TPL"]'
    
    # Or with custom quantity multiplier
    bench --site teksons.dev execute tekson_manufacturing.scripts.create_opening_stock.create_opening_stock --args '["Stores - TPL", 100]'
"""

import frappe
from frappe import _
from datetime import datetime


def get_all_bom_components():
    """
    Get all unique raw material components from all submitted BOMs
    
    Returns: dict of {item_code: total_qty_required}
    """
    print("=" * 80)
    print("FETCHING BOM COMPONENTS")
    print("=" * 80)
    
    # Get all submitted BOMs
    boms = frappe.get_all('BOM', 
        filters={'docstatus': 1, 'is_active': 1},
        fields=['name', 'item', 'quantity']
    )
    
    print(f"Found {len(boms)} active submitted BOMs")
    
    # Collect all BOM items
    components = {}
    for bom in boms:
        bom_doc = frappe.get_doc('BOM', bom.name)
        print(f"\nBOM: {bom.name} → {bom.item} (Qty: {bom.quantity})")
        
        for item in bom_doc.items:
            item_code = item.item_code
            qty = item.qty
            
            # Check if this is a raw material (no BOM of its own)
            has_bom = frappe.db.exists('BOM', {
                'item': item_code, 
                'is_active': 1, 
                'docstatus': 1
            })
            
            if has_bom:
                print(f"  ⊕ {item_code} (Qty: {qty}) → Sub-Assembly (has own BOM)")
            else:
                print(f"  → {item_code} (Qty: {qty}) → Raw Material")
                if item_code not in components:
                    components[item_code] = 0
                components[item_code] += qty
    
    print(f"\nTotal unique raw materials: {len(components)}")
    return components


def create_opening_stock(warehouse="Stores - TPL", qty_multiplier=100, submit=True):
    """
    Create Material Receipt Stock Entry for opening stock
    
    Args:
        warehouse: Target warehouse (default: Stores - TPL)
        qty_multiplier: Multiplier for BOM qty to get reasonable stock (default: 100)
        submit: Whether to submit the Stock Entry
    
    Returns: Stock Entry document
    """
    print("\n" + "=" * 80)
    print("CREATING OPENING STOCK ENTRY")
    print("=" * 80)
    print(f"Warehouse: {warehouse}")
    print(f"Qty Multiplier: {qty_multiplier}x")
    print()
    
    # Get all BOM components
    components = get_all_bom_components()
    
    if not components:
        print("❌ No BOM components found!")
        return None
    
    # Create Stock Entry
    stock_entry = frappe.new_doc('Stock Entry')
    stock_entry.stock_entry_type = 'Material Receipt'
    stock_entry.posting_date = datetime.now().strftime('%Y-%m-%d')
    stock_entry.posting_time = datetime.now().strftime('%H:%M:%S')
    stock_entry.to_warehouse = warehouse
    
    print("\nAdding items to Stock Entry:")
    print("-" * 80)
    
    for item_code, base_qty in sorted(components.items()):
        # Calculate qty (base qty * multiplier for reasonable stock)
        qty = base_qty * qty_multiplier
        
        # Get item details
        item = frappe.get_doc('Item', item_code)
        
        stock_entry.append('items', {
            'item_code': item_code,
            'item_name': item.item_name or item_code,
            'description': item.description or item_code,
            'qty': qty,
            'basic_rate': 0,  # Set to 0 or actual rate
            'amount': 0,
            't_warehouse': warehouse,
            'allow_zero_valuation_rate': 1
        })
        
        print(f"  ✓ {item_code}: {qty} units")
    
    print(f"\nTotal items: {len(stock_entry.items)}")
    print("-" * 80)
    
    # Save
    stock_entry.insert()
    print(f"\n✅ Stock Entry created: {stock_entry.name}")
    
    # Submit
    if submit:
        stock_entry.submit()
        print(f"✅ Stock Entry submitted: {stock_entry.name}")
        
        # Verify stock
        print(f"\nVerifying stock in {warehouse}...")
        for item in stock_entry.items:
            bin = frappe.get_value('Bin', 
                {'item_code': item.item_code, 'warehouse': warehouse},
                'actual_qty')
            print(f"  {item.item_code}: {bin or 0} units")
    
    return stock_entry


def create_minimal_opening_stock(warehouse="Stores - TPL", submit=True):
    """
    Create minimal opening stock (just 10 units per item) for testing
    
    Args:
        warehouse: Target warehouse
        submit: Whether to submit
    
    Returns: Stock Entry document
    """
    print("\n" + "=" * 80)
    print("CREATING MINIMAL OPENING STOCK (10 units per item)")
    print("=" * 80)
    
    # Get all BOM components
    components = get_all_bom_components()
    
    if not components:
        print("❌ No BOM components found!")
        return None
    
    # Create Stock Entry
    stock_entry = frappe.new_doc('Stock Entry')
    stock_entry.stock_entry_type = 'Material Receipt'
    stock_entry.posting_date = datetime.now().strftime('%Y-%m-%d')
    stock_entry.posting_time = datetime.now().strftime('%H:%M:%S')
    stock_entry.to_warehouse = warehouse
    
    print(f"\nAdding {len(components)} items with 10 units each...")
    
    for item_code in sorted(components.keys()):
        item = frappe.get_doc('Item', item_code)
        
        stock_entry.append('items', {
            'item_code': item_code,
            'item_name': item.item_name or item_code,
            'description': item.description or item_code,
            'qty': 10,
            'basic_rate': 0,
            'amount': 0,
            't_warehouse': warehouse,
            'allow_zero_valuation_rate': 1
        })
    
    # Save
    stock_entry.insert()
    print(f"✅ Stock Entry created: {stock_entry.name}")
    
    # Submit
    if submit:
        stock_entry.submit()
        print(f"✅ Stock Entry submitted: {stock_entry.name}")
    
    return stock_entry
