import os
from PIL import Image, ImageDraw, ImageFont

def generate_keybeam_icon(output_path="icon.ico"):
    # Create a list of sizes for multi-resolution ICO file
    sizes = [16, 32, 48, 64, 128, 256]
    images = []

    for size in sizes:
        # Create an image with transparent background
        img = Image.new("RGBA", (size, size), color=(0, 0, 0, 0))
        d = ImageDraw.Draw(img)

        # Draw a rounded rect background with deep dark-blue color
        margin = max(1, size // 16)
        radius = max(2, size // 8)
        
        # Draw background rounded box
        d.rounded_rectangle(
            [margin, margin, size - margin, size - margin],
            radius=radius,
            fill=(9, 10, 15, 255),  # deep space dark background color
            outline=(0, 255, 127, 255),  # neon green outline
            width=max(1, size // 24)
        )

        # Draw scanning laser line (horizontal neon red line across the middle)
        laser_y = size // 2
        d.line(
            [(margin * 2, laser_y), (size - margin * 2, laser_y)],
            fill=(255, 46, 99, 255),  # neon red
            width=max(1, size // 32)
        )

        # Draw letters "K" and "B" (neon green text)
        try:
            # Try to load a font, fallback to default font
            font_size = int(size * 0.4)
            # Use default PIL font (it works at all sizes but is tiny, so we can draw paths or draw blocks)
            # Drawing a retro block-like K and B using lines is extremely crisp and retro!
            # Let's draw block letter paths manually for clean vector scaling!
            scale = size / 256.0
            
            # K character left stem
            d.rectangle([int(70*scale), int(70*scale), int(90*scale), int(186*scale)], fill=(0, 255, 127, 255))
            # K branches
            d.line([int(90*scale), int(128*scale), int(150*scale), int(70*scale)], fill=(0, 255, 127, 255), width=int(18*scale))
            d.line([int(90*scale), int(128*scale), int(150*scale), int(186*scale)], fill=(0, 255, 127, 255), width=int(18*scale))

            # B character left stem
            d.rectangle([int(150*scale), int(70*scale), int(170*scale), int(186*scale)], fill=(0, 255, 127, 255))
            # B loops
            d.arc([int(150*scale), int(70*scale), int(210*scale), int(128*scale)], start=270, end=90, fill=(0, 255, 127, 255), width=int(18*scale))
            d.arc([int(150*scale), int(128*scale), int(210*scale), int(186*scale)], start=270, end=90, fill=(0, 255, 127, 255), width=int(18*scale))
        except Exception:
            # Simple geometric fallback: draw a green crosshair
            d.ellipse([size//3, size//3, 2*size//3, 2*size//3], fill=(0, 255, 127, 255))

        images.append(img)

    # Save as multi-resolution ICO file
    images[0].save(
        output_path,
        format="ICO",
        sizes=[(size, size) for size in sizes],
        append_images=images[1:]
    )
    print(f"Generated multi-resolution ICO file at: {output_path}")

if __name__ == "__main__":
    generate_keybeam_icon()
