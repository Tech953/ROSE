"""Compare preserved and current indexed frames at the same registered world scale."""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]


def main():
    before=json.loads((ROOT/'art-source/archive/rendered-v4/art-manifest-rendered.json').read_text())
    after=json.loads((ROOT/'static/art-manifest-rendered.json').read_text())
    canvas=Image.new('RGB',(1180,2760),'#121b16');draw=ImageDraw.Draw(canvas)
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf',18)
    small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf',13)
    draw.text((24,20),'ROSE / PREFAB REFERENCE PASS / SAME WORLD SCALE',font=font,fill='#dac6ab')
    draw.text((24,51),'Prepared indexed frames at equal world scale, with registered feet',font=small,fill='#9db39b')
    rows=[('ROOT-GROWN WORKSHOP / FITTED CLADDING AND REPAIRS','workshop_WN_TOWER','idle'),('CITY WORKSHOP / PANELS AND SERVICE DETAILS','workshop_CITY_CLOUD_S','idle'),('HILLS WORKSHOP / MASONRY AND SURFACE WEAR','workshop_ENACT_HILLS','idle'),('CITY EXCHANGE / COUNTER BOARDS AND STOCK','exchange_CITY_CLOUD_S','idle'),('BIOME OBSTACLE / ERODED STONE AND SCREE','rock_WN_TOWER','idle'),('BIOME FLOOR / FINER GRANULAR RELIEF','ground_WN_TOWER','idle')]
    for row,(title,key,clip) in enumerate(rows):
        y=82+row*416;draw.text((24,y),title,font=small,fill='#ccbda2')
        for column,manifest in enumerate([before,after]):
            x=24+column*578;panel_height=538 if key.startswith('ground_') else 378;panel=Image.new('RGB',(554,panel_height),'#273026');p=ImageDraw.Draw(panel)
            p.text((14,12),'0.7 / PRESERVED' if column==0 else '0.8 / REFERENCE PASS',font=small,fill='#b6c6ac')
            asset=manifest['assets'][key];index=asset['clips'][clip][0];sx,sy,w,h=asset['frames'][index]
            with Image.open(ROOT/'static'/asset['image'].lstrip('/')) as sheet:frame=sheet.crop((sx,sy,sx+w,sy+h)).convert('RGBA')
            factor=asset['scale']*3
            frame=frame.resize((round(w*factor),round(h*factor)),Image.Resampling.NEAREST)
            if key.startswith('ground_'):
                # Both central relief samples fill the same physical image size.
                panel.paste(frame,((554-frame.width)//2,39))
            else:
                anchor=[value*factor for value in asset['anchor']]
                panel.paste(frame,(round(277-anchor[0]),round(240-anchor[1])),frame)
            canvas.paste(panel,(x,y+25));draw.rectangle((x,y+25,x+553,y+24+panel_height),outline='#485344')
    canvas.save(ROOT/'docs/Rose-fidelity-comparison.png')


if __name__=='__main__':main()
