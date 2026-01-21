"""Simple test of vsdx library"""
from vsdx import VisioFile

# Try to create a simple Visio file
try:
    print("Testing vsdx library...")
    
    # Create a new Visio file
    vis = VisioFile()
    print(f"Created VisioFile: {vis}")
    print(f"Pages: {vis.pages}")
    
    if vis.pages:
        page = vis.pages[0]
        print(f"First page: {page}")
        print(f"Page name: {page.name}")
    
    # Try to save
    vis.save_vsdx("test_output.vsdx")
    print("Saved test_output.vsdx successfully!")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
