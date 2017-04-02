from xml.dom import minidom

class XMLParser:
    
    def __init__(self):
        self.contentStr = ""
        self.titleStr = ""
        self.sourceStr = ""
        self.content_type = ""
        self.court = ""
        self.domain = ""
        self.jurisdictionArr = []
        self.tagArr = []
        self.areaOfLawArr = []
        self.date = ""

    def reset(self):
        self.contentStr = ""
        self.titleStr = ""
        self.sourceStr = ""
        self.contentType = ""
        self.court = ""
        self.domain = ""
        self.jurisdictionArr = []
        self.tagArr = []
        self.areaOfLawArr = []
        self.date = ""

    def parseDoc(self, filename):
        self.reset()
        self.xmlDocObject = minidom.parse(filename)
        self.strNodeList = self.xmlDocObject.getElementsByTagName('str')
        self.arrNodeList = self.xmlDocObject.getElementsByTagName('arr')
        dateArr = self.xmlDocObject.getElementsByTagName('date')

        # Fill in string nodes' zone
        for strNode in self.strNodeList:
            if self.nodeHasNameTag(strNode):
                namedNode = strNode.attributes["name"]
                if namedNode.value == "content":
                    self.contentStr = self.getText(strNode.childNodes)
                elif namedNode.value == "title":
                    self.titleStr = self.getText(strNode.childNodes)
                elif namedNode.value == "source_type":
                    self.sourceStr = self.getText(strNode.childNodes)
                elif namedNode.value == "content_type":
                    self.content_type = self.getText(strNode.childNodes)
                elif namedNode.value == "court":
                    self.court = self.getText(strNode.childNodes)
                elif namedNode.value == "domain":
                    self.domain = self.getText(strNode.childNodes)

        # Fill in array nodes' zone
        for arrNode in self.arrNodeList:
            if self.nodeHasNameTag(arrNode):
                namedNode = arrNode.attributes["name"]
                if namedNode.value == "jurisdiction":
                    self.jurisdictionArr = self.getArray(arrNode.getElementsByTagName('str'))
                elif namedNode.value == "tag":
                    self.tagArr = self.getArray(arrNode.getElementsByTagName('str'))
                elif namedNode.value == "areaoflaw":
                    self.areaOfLawArr = self.getArray(arrNode.getElementsByTagName('str'))

        for dateNode in dateArr:
            if self.nodeHasNameTag(dateNode):
                namedNode = dateNode.attributes["name"]
                if namedNode.value == "date_posted":
                    self.date = self.getText(dateNode.childNodes)
                if namedNode.value == "date_modified":
                    self.date = self.getText(dateNode.childNodes)

    def nodeHasNameTag(self, node):
        return (node.attributes.get("name", "empty") != "empty")

    def getText(self, nodelist):
        rc = []
        for node in nodelist:
            if node.nodeType == node.TEXT_NODE:
                rc.append(node.data)
                return ''.join(rc)

    def getArray(self, nodelist):
        arr = []
        for node in nodelist:
            arr.append(self.getText(node.childNodes))
        return arr