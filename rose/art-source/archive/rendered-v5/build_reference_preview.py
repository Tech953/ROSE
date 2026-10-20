"""Show Rose's eight original indexed terrain samples at exact 2x pixels."""
import json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[1]


def main():
    m=json.loads((ROOT/'static/art-manifest-rendered.json').read_text())
    canvas=Image.new('RGB',(1760,1210),'#141d18');d=ImageDraw.Draw(canvas)
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf',18)
    small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf',13)
    d.text((25,20),'ROSE 0.8 / REGIONAL FIELD AND PATH SURFACES',font=font,fill='#dac6ab')
    d.text((25,50),'Original Blender relief / shared indexed palette / actual exported pixels at 2x',font=small,fill='#a7b59d')
    for column,region in enumerate(m['visual_catalog']['regions']):
        x=25+column*435;d.text((x,90),region,font=small,fill='#cebaa1')
        for row,prefix in enumerate(['ground_','ground_path_']):
            y=130+row*550;a=m['assets'][prefix+region];sx,sy,w,h=a['frames'][0]
            d.text((x,y-22),'FIELD' if row==0 else 'PATH / EXISTING TRAVEL TILES',font=small,fill='#a7b59d')
            with Image.open(ROOT/'static'/a['image'].lstrip('/')) as sheet:
                f=sheet.crop((sx,sy,sx+w,sy+h)).convert('RGBA').convert('RGB').resize((w*2,h*2),Image.Resampling.NEAREST)
            canvas.paste(f,(x,y));d.rectangle((x,y,x+f.width-1,y+f.height-1),outline='#485344')
    canvas.save(ROOT/'docs/Rose-prefab-reference-preview.png')


if __name__=='__main__':main()
