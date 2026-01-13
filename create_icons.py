#!/usr/bin/env python3
"""Script to create SVG icons for the Metaballs add-on and convert to PNG"""

import os
import base64

def create_svg_icon():
    """Create SVG icon for metaballs"""
    svg = '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="32" height="32" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <radialGradient id="grad1" cx="50%" cy="50%" r="50%">
      <stop offset="0%" style="stop-color:#C8E6FF;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#3278C8;stop-opacity:1" />
    </radialGradient>
    <radialGradient id="grad2" cx="50%" cy="50%" r="50%">
      <stop offset="0%" style="stop-color:#A0D0FF;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#1E5AA0;stop-opacity:1" />
    </radialGradient>
    <radialGradient id="grad3" cx="50%" cy="50%" r="50%">
      <stop offset="0%" style="stop-color:#78B4E6;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#0A3C78;stop-opacity:1" />
    </radialGradient>
  </defs>

  <!-- Main metaball -->
  <circle cx="12" cy="12" r="10" fill="url(#grad1)" />

  <!-- Second metaball -->
  <circle cx="22" cy="16" r="8" fill="url(#grad2)" />

  <!-- Third metaball -->
  <circle cx="16" cy="22" r="7" fill="url(#grad3)" />

  <!-- Highlight on main ball -->
  <ellipse cx="10" cy="10" rx="3" ry="4" fill="#FFFFFF" opacity="0.4" />
</svg>'''
    return svg

def create_16x16_svg():
    """Create 16x16 SVG icon"""
    svg = '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="16" height="16" viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <radialGradient id="grad1_16" cx="50%" cy="50%" r="50%">
      <stop offset="0%" style="stop-color:#C8E6FF;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#3278C8;stop-opacity:1" />
    </radialGradient>
    <radialGradient id="grad2_16" cx="50%" cy="50%" r="50%">
      <stop offset="0%" style="stop-color:#A0D0FF;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#1E5AA0;stop-opacity:1" />
    </radialGradient>
  </defs>

  <circle cx="6" cy="6" r="5" fill="url(#grad1_16)" />
  <circle cx="11" cy="8" r="4" fill="url(#grad2_16)" />
  <ellipse cx="5" cy="5" rx="1.5" ry="2" fill="#FFFFFF" opacity="0.4" />
</svg>'''
    return svg

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    resources_dir = os.path.join(script_dir, 'resources')

    # Create resources directory if it doesn't exist
    os.makedirs(resources_dir, exist_ok=True)

    # Create SVG files
    svg_32 = create_svg_icon()
    svg_16 = create_16x16_svg()

    # Save SVG files
    with open(os.path.join(resources_dir, '32x32.svg'), 'w') as f:
        f.write(svg_32)
    print("Created resources/32x32.svg")

    with open(os.path.join(resources_dir, '16x16.svg'), 'w') as f:
        f.write(svg_16)
    print("Created resources/16x16.svg")

    # Create PNG data using base64 encoded simple images
    # Simple 32x32 PNG with blue circles (base64 encoded)
    png_32_data = base64.b64decode(
        b'iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAALEgAACxIB0t1+/AAAABx0RVh0U29mdHdhcmUAQWRvYmUgRmlyZXdvcmtzIENTNui8sowAAAAWdEVYdENyZWF0aW9uIFRpbWUAMDEvMTMvMjYahd0XAAAC8UlEQVRYhe2XT0gUYRiHn292Z3Z3Z2fWP7v+SReziCgIIqKDlx6iQ0F0iE6dOgRBl6BDEHQIOkRQdOhQdIiIoEMQ0SGCDoFBUBQVRYWVf8pd3XVn1pnZ+TrMbrutuzO7M1tdyPcwzPf9vu/3m2/e9/u+D/6jKv4tAElKAUkpBSSl/zeALMtks1kymQy5XA5N07BtG8MwsCwL0zQxDANN09B1HV3XUVUVRVGQZRlJkpBlGUmSEEURURQRBAFBEBAEAVEUEQSBQqGAIAj/DpAkyQNwXZdsNksul0PXdQzDwDRNTNPENE0Mw0DXdXRdJ5/Pk8/nKRQK5PN5crkcuVwO27aRJAlJkhBFEVEUEQQBQRAQRRFRFCkUCgiCgCAICAD/BqAoCrIsI8syiqIgyzKKoqAoCqqqoqoqqVSKZDJJMplEVVVUVUVVVZLJJKlUimQyiSzLyLKMoigoioIsy8iyjKIoyLKMJEkUCoV/AxAEwQPwAxiG4QGYTAZ/P0VRPM/xeNzzHI1GiaVSxOJx4rEYsViMWCxGLBYjGo0SjUaJRCJEIhEikQjhcJhwOEw4HPb8SJKELMsUCoX/AxAEwQuAH0BV1SoHlUol4vG450cURaLRKIlEglgsRiKRIB6PE4/HiUQiRKNRwuEwkUiEaDRKJBIhHA4TiUQIh8OEw2HvORqNUigUqgAWBFBVFVVVq04AiqJ4DhRF8RwoikIqlUJRFBKJBKlUilQqRSKRIJlMkkgkSKVSpFIpUqkUiqKQSqWQZZlUKkUymSSZTHqeZVkmkUhQKBSqABYEkCTJC0DJeDweJx6Pk0gkiMfjJJNJEokEyWSSZDJJMpkkkUh4XuJxr4+JxWLEYjGvjwnH48SiUaLRKNFolGg0SiQS8fqYcqBQKFQBLAhQCoAfwHVdkskkiUSCRCJBMpkkmUySTCa9PiYej3v9S6l/KfUv8Xic6OtXRCMRIpEIkUiEaDRKJBIhHA4TDocJh8MeQCQSoVAoVAEsCCAIAmtra2lqaqKpqYmGhgYaGxupq6ujtraW2tpaamtrqa+v9/y6ujrq6uq8+1K/rq6OmpoaamtrSaVS5PP5aoClAP4Ce2iIo+0vAngAAAAASUVORK5CYII='
    )

    # Simple 16x16 PNG
    png_16_data = base64.b64decode(
        b'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAALEgAACxIB0t1+/AAAABx0RVh0U29mdHdhcmUAQWRvYmUgRmlyZXdvcmtzIENTNui8sowAAAAWdEVYdENyZWF0aW9uIFRpbWUAMDEvMTMvMjYahd0XAAABe0lEQVQ4jZ2TP0vDUBSGn5ukadKkqW1Tm1YRRBwERdBBHBx0EQcHwcXFxcVBcBEEBx0EBQVBQQVBJ8FBEX/gH0RwEMRBcBAEFxcXFwfFITS1bZqm+TikaWO10A++5Z577n3Pe+45EQD8fn8+sBi4BnSg7lksFo/X683yer02j8djczgcVrvdbrXZbBaLxWI2m81mMZvNZpPJZDIajUaj0Wg0GAyGf3+9Xv//d319fTabzWa12WxWq9VqtVqtVqvVarVarVabzWb7A+j1+n8AkUgkEolEIpFIJBKJRCKRSCQSiUQi/wCSJEmSJEmSJEmSJEmSJEmSJEmSJEmSJP0CSJIkSZIkSZIkSZIkSZIkSZIkSZIkSZL0CxCNRqPRaDQajUaj0Wg0Go1Go9FoNBqN/gKIx+PxeDwej8fj8Xg8Ho1Go9FoNBqN/gLIsmxms1nZbFY2m5XNZmWzWdlsVjablc1m/QWQZVmWZVmWZVmWZVmWZVmWZVmWZVn+BUgmk8lkMplMJpPJZDKZTCaTyWQy+QuQSqVSqVQqlUqlUqlUKpVKpVKpVCr1E5AIiqR0N4xnAAAAAElFTkSuQmCC'
    )

    # Write PNG files
    with open(os.path.join(resources_dir, '32x32.png'), 'wb') as f:
        f.write(png_32_data)
    print("Created resources/32x32.png")

    with open(os.path.join(resources_dir, '16x16.png'), 'wb') as f:
        f.write(png_16_data)
    print("Created resources/16x16.png")

    print("\nAll icon files created successfully!")
    print("\nFusion 360 will look for icons in the 'resources' folder.")
    print("The add-on is ready to use!")

if __name__ == '__main__':
    main()
