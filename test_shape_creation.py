"""Test creating and copying shapes in Visio"""
from vsdx import VisioFile
import shutil

# Copy template to test file
shutil.copy2("TGN-v2.0-Template.vsdx", "test_shape_creation.vsdx")

try:
    vis = VisioFile("test_shape_creation.vsdx")
    page = vis.pages[1]  # Use Demo page
    
    print(f"Page: {page.name}")
    print(f"Initial shapes: {len(page.all_shapes)}")
    
    # Get first shape (header) to use as template
    if page.all_shapes:
        template_shape = page.all_shapes[0]
        print(f"\nTemplate shape text: {template_shape.text}")
        print(f"Template shape position: x={template_shape.x}, y={template_shape.y}")
        print(f"Template shape size: w={template_shape.width}, h={template_shape.height}")
        
        # Try to copy the shape
        print("\nAttempting to copy shape...")
        new_shape = template_shape.copy(page)
        
        if new_shape:
            print(f"Successfully copied shape!")
            print(f"New shape ID: {new_shape.ID}")
            
            # Try to modify the copied shape
            print("\nModifying copied shape...")
            new_shape.text = "TEST DEVICE 1"
            new_shape.x = 5.0
            new_shape.y = 5.0
            new_shape.width = 2.0
            new_shape.height = 1.0
            
            print(f"Modified shape text: {new_shape.text}")
            print(f"Modified shape position: x={new_shape.x}, y={new_shape.y}")
            
            # Save the file
            vis.save_vsdx("test_shape_creation.vsdx")
            print("\nSaved test file successfully!")
            print("Check test_shape_creation.vsdx to see if the shape was added")
        else:
            print("Failed to copy shape")
    
    print(f"\nFinal shapes: {len(page.all_shapes)}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
