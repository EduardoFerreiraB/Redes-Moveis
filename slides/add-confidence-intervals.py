"""Add native custom error bars to the Artifact Tool draft, using the CSV-derived CIs.

The presentation API exposes only constant/statistical error bars. OOXML custom
arrays preserve the independently calculated t confidence interval at each speed.
"""
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / 'tmp/slides-build'
NS = {'c': 'http://schemas.openxmlformats.org/drawingml/2006/chart',
      'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'}
for prefix, uri in NS.items():
    ET.register_namespace(prefix, uri)
ET.register_namespace('r', 'http://schemas.openxmlformats.org/officeDocument/2006/relationships')


def node(parent, tag, attrs=None, text=None):
    e = ET.SubElement(parent, '{' + NS[tag[0]] + '}' + tag[2:], attrs or {})
    if text is not None:
        e.text = str(text)
    return e


errors = json.loads((BUILD / 'chart-errors.json').read_text())
changed = 0
with ZipFile(BUILD / 'draft.pptx') as zin, ZipFile(BUILD / 'candidate.pptx', 'w', ZIP_DEFLATED) as zout:
    for entry in zin.infolist():
        content = zin.read(entry.filename)
        matches = [e for e in errors if entry.filename.endswith(f"/charts/chart{e['index']}.xml")]
        if matches:
            changed += 1
            root = ET.fromstring(content)
            series = root.findall('.//c:scatterChart/c:ser', NS)
            assert len(series) == 3
            for ser, spec in zip(series, matches[0]['series']):
                old = ser.find('c:errBars', NS)
                if old is not None:
                    ser.remove(old)
                bar = ET.Element('{' + NS['c'] + '}errBars')
                for tag, val in [('errDir', 'y'), ('errBarType', 'both'), ('errValType', 'cust'), ('noEndCap', '0')]:
                    node(bar, 'c:' + tag, {'val': val})
                for sign in ['plus', 'minus']:
                    lit = node(node(bar, 'c:' + sign), 'c:numLit')
                    node(lit, 'c:formatCode', text='0.000000')
                    node(lit, 'c:ptCount', {'val': '4'})
                    for i, value in enumerate(spec['ci']):
                        node(node(lit, 'c:pt', {'idx': str(i)}), 'c:v', text=value)
                line = node(node(bar, 'c:spPr'), 'a:ln', {'w': '12700'})
                node(node(line, 'a:solidFill'), 'a:srgbClr', {'val': spec['color'].lstrip('#')})
                ser.insert(list(ser).index(ser.find('c:xVal', NS)), bar)
            content = ET.tostring(root, encoding='utf-8', xml_declaration=True)
        zout.writestr(entry, content)
assert changed == len(errors), (changed, len(errors))
print(f'Added custom 95% CIs to {changed} native charts')
