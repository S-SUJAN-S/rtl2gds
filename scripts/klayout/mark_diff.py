from PIL import Image, ImageChops, ImageDraw

# Load the zoomed floorplan and placement images
img1 = Image.open("/mnt/c/Users/ssuja/OneDrive/Desktop/Learn_Antigravity_Advance/rtl-2-gds-automation/full-adder-test/images/floorplan_zoomed.png").convert("RGB")
img2 = Image.open("/mnt/c/Users/ssuja/OneDrive/Desktop/Learn_Antigravity_Advance/rtl-2-gds-automation/full-adder-test/images/placement_zoomed.png").convert("RGB")

# Calculate the absolute difference between the two images
diff = ImageChops.difference(img1, img2)

# Get bounding box of the non-zero difference
bbox = diff.getbbox()

if bbox:
    print(f"Found differences at bounding box: {bbox}")
    
    # Draw a bright red circle around the difference on the placement image
    draw = ImageDraw.Draw(img2)
    
    # Expand the bounding box slightly for visual clarity
    padding = 20
    expanded_bbox = (
        max(0, bbox[0] - padding),
        max(0, bbox[1] - padding),
        min(img2.width, bbox[2] + padding),
        min(img2.height, bbox[3] + padding)
    )
    
    # Draw a bold red ellipse (circle) around the region
    draw.ellipse(expanded_bbox, outline="red", width=8)
    
    # Save the marked image
    output_path = "/mnt/c/Users/ssuja/.gemini/antigravity/brain/2b36d849-7095-4862-916d-9f895f1b40c8/placement_diff_marked.png"
    img2.save(output_path)
    
    # Also save to user directory
    img2.save("/mnt/c/Users/ssuja/OneDrive/Desktop/Learn_Antigravity_Advance/rtl-2-gds-automation/full-adder-test/images/placement_diff_marked.png")
    
    print(f"Saved marked image to {output_path}")
else:
    print("No differences found. They are still identical.")
