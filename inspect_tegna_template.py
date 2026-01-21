"""Inspect the TEGNA Visio template"""
from vsdx import VisioFile

template_file = "TEGNA-NETWORK-Template.vsdx"

try:
    print(f"Opening template: {template_file}")
    print("=" * 70)
    
    vis = VisioFile(template_file)
    
    print(f"\nPages: {len(vis.pages)}")
    for i, page in enumerate(vis.pages):
        print(f"  Page {i}: {page.name}")
        print(f"    Shapes: {len(page.all_shapes)}")
        
        # Show first few shapes
        if page.all_shapes:
            print(f"    First 10 shapes:")
            for j, shape in enumerate(page.all_shapes[:10]):
                text = shape.text if hasattr(shape, 'text') else 'No text'
                print(f"      Shape {j}: {text[:50]}")
    
    # Check for master shapes
    print("\n" + "=" * 70)
    print("Checking for master shapes...")
    
    if hasattr(vis, 'masters') and vis.masters:
        print(f"Masters found: {len(vis.masters)}")
        for i, master in enumerate(vis.masters[:20]):
            print(f"  Master {i}: {master}")
    else:
        print("No masters found or not accessible")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
