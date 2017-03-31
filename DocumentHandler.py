from xml.dom import minidom

document = """  <doc>
    <str name="document_id">1585740</str>
    <str name="title">[1997] 1 SLR(R) 914 - Lim Kitt Ping Lynnette v People's Insurance Co Ltd and another</str>
    <str name="url">http://www.singaporelaw.sg/sglaw/images/ArbitrationCases/%5B1997%5D_1_SLR(R)_0914.pdf</str>
    </doc>"""

def getText(nodelist):
    rc = []
    for node in nodelist:
      if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
            return ''.join(rc)

xmldoc = minidom.parse("sampleDoc.xml")
print('parsing success')
itemlist = xmldoc.getElementsByTagName('str')
for item in itemlist:
      print item.attributes["name"].value, ": ", getText(item.childNodes)
