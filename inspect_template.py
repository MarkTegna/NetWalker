"""Inspect the TGN Visio template to see what shapes are available"""
from vsdx import VisioFile

template_file = "TGN-v2.0-Template.vsdx"

try:
    print(f"Opening template: {template_file}")
    print("=" * 70)
    
    vis = VisioFile(template_file)
    
    print(f"\nPages: {len(vis.pages)}")
    for i, page in enumerate(vis.pages):
        print(f"  Page {i}: {page.name}")
        print(f"    Width: {page.width}, Height: {page.height}")
        print(f"    Is Master Page: {page.is_master_page}")
        print(f"    Shapes: {len(page.shapes)}")
        
        # Show first few shapes
        if page.shapes:
            print(f"    First 10 shapes:")
            for j, shape in enumerate(page.shapes[:10]):
                print(f"      Shape {j}: {shape.text if hasattr(shape, 'text') else 'No text'}")
                if hasattr(shape, 'master_shape'):
                    print(f"        Master: {shape.master_shape}")
                if hasattr(shape, 'ID'):
                    print(f"        ID: {shape.ID}")
    
    # Check for master shapes/stencils
    print("\n" + "=" * 70)
    print("Checking for master shapes...")
    
    if hasattr(vis, 'masters'):
        print(f"Masters found: {len(vis.masters) if vis.masters else 0}")
        if vis.masters:
            for master in vis.masters[:10]:
                print(f"  - {master}")
    
    # Check all shapes in the file
    print("\n" + "=" * 70)
    print("All shapes in template:")
    all_shapes = vis.pages[0].all_shapes if vis.pages else []
    print(f"Total shapes: {len(all_shapes)}")
    
    for i, shape in enumerate(all_shapes[:20]):  # First 20 shapes
        print(f"\nShape {i}:")
        print(f"  Text: {shape.text if hasattr(shape, 'text') else 'N/A'}")
        print(f"  ID: {shape.ID if hasattr(shape, 'ID') else 'N/A'}")
        
        # Check for useful attributes
        attrs = ['x', 'y', 'width', 'height', 'master_shape', 'master_page']
        for attr in attrs:
            if hasattr(shape, attr):
                val = getattr(shape, attr)
                print(f"  {attr}: {val}")
    
    # Try to find shapes we can copy
    print("\n" + "=" * 70)
    print("Looking for copyable device shapes...")
    
    # Look for shapes with specific text or properties
    device_shapes = []
    for shape in all_shapes:
        text = shape.text if hasattr(shape, 'text') else ''
        if text and any(keyword in text.upper() for keyword in ['DEVICE', 'SWITCH', 'ROUTER', 'CORE', 'IDF', 'MDF']):
            device_shapes.append(shape)
            print(f"  Found potential device shape: {text[:50]}")
    
    print(f"\nTotal potential device shapes: {len(device_shapes)}")
    
    # Check if we can copy shapes
    print("\n" + "=" * 70)
    print("Checking shape copy capabilities...")
    
    if all_shapes:
        test_shape = all_shapes[0]
        print(f"Test shape methods: {[m for m in dir(test_shape) if not m.startswith('_') and 'copy' in m.lower()]}")
        print(f"Test shape methods (all): {[m for m in dir(test_shape) if not m.startswith('_')][:20]}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
