PROPERTIES_TO_EXTRACT = {
    "id": {
        "xpaths": [
            ".//dc:identifier",
            ".//gmd:fileIdentifier/gco:CharacterString"
        ],
        "urn": "urn:li:structuredProperty:37a61c93-b1aa-4261-90e8-947771c3582b"
    },
    "date": {
        "xpaths": [
            ".//dc:date",
            ".//gmd:dateStamp/gco:Date",
            ".//gmd:citation//gmd:date/gco:Date"
        ],
        "urn": "urn:li:structuredProperty:be175e19-c07a-40ab-8228-52094c78edd8"
    },
    "language": {
        "xpaths": [
            ".//dc:language",
            ".//gmd:language/gmd:LanguageCode"  # ojo: este es atributo @codeListValue
        ],
        "urn": "urn:li:structuredProperty:acdd5c4c-5463-47b5-a748-55d9955c776d"
    },
    "type": {
        "xpaths": [
            ".//dc:type",
            ".//gmd:hierarchyLevel/gmd:MD_ScopeCode"  # ojo: atributo codeListValue
        ],
        "urn": "urn:li:structuredProperty:dce65839-7577-4ddf-881c-95df4c30a514"
    }
}
