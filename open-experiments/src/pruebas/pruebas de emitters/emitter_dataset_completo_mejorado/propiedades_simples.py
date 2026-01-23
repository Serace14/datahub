PROPERTIES_TO_EXTRACT = [
    {
        "name": "id",
        "type": "structuredProperty",
        "property_urn": "urn:li:structuredProperty:37a61c93-b1aa-4261-90e8-947771c3582b",
        "xpaths": [
            ".//dc:identifier",
            ".//gmd:fileIdentifier/gco:CharacterString"
        ]
    },
    {
        "name": "boundingbox",
        "type": "structuredProperty",
        "property_urn": "urn:li:structuredProperty:boundingbox",
        "xpaths": [
            ".//ows:BoundingBox",
            ".//gmd:EX_GeographicBoundingBox"
        ]
    },
    {
        "name": "date",
        "type": "structuredProperty",
        "property_urn": "urn:li:structuredProperty:be175e19-c07a-40ab-8228-52094c78edd8",
        "xpaths": [
            ".//dc:date",
            ".//gmd:dateStamp/gco:Date",
            ".//gmd:citation//gmd:date/gco:Date"
        ]
    },
    {
        "name": "language",
        "type": "structuredProperty",
        "property_urn": "urn:li:structuredProperty:acdd5c4c-5463-47b5-a748-55d9955c776d",
        "xpaths": [
            ".//dc:language",
            ".//gmd:language/gmd:LanguageCode/@codeListValue"
        ]
    },
    {
        "name": "owners",
        "type": "ownership",
        "xpaths": [
            ".//gmd:pointOfContact//gmd:organisationName//gco:CharacterString"
        ],
        "owner_type": "TECHNICAL_OWNER"
    },
    {
        "name": "rights",
        "type": "structuredProperty",
        "property_urn": "urn:li:structuredProperty:rights",
        "xpaths": [
            ".//dc:rights",
            ".//gmd:resourceConstraints//gmd:MD_LegalConstraints//gmd:accessConstraints//gmd:MD_RestrictionCode/@codeListValue",
            ".//gmd:resourceConstraints//gmd:MD_LegalConstraints//gmd:useConstraints//gmd:MD_RestrictionCode/@codeListValue",
            ".//gmd:resourceConstraints//gmd:MD_LegalConstraints//gmd:otherConstraints//gco:CharacterString"
        ]
    },
    {
        "name": "tags",
        "type": "tags",
        "xpaths": [
            ".//gmd:keyword/gco:CharacterString"
        ]
    },
    {
        "name": "type",
        "type": "structuredProperty",
        "property_urn": "urn:li:structuredProperty:dce65839-7577-4ddf-881c-95df4c30a514",
        "xpaths": [
            ".//dc:type",
            ".//gmd:hierarchyLevel/gmd:MD_ScopeCode/@codeListValue"
        ]
    },
    {
        "name": "urls",
        "type": "structuredProperty",
        "property_urn": "urn:li:structuredProperty:c4fe8236-87ff-4310-ac79-6468b4633634",
        "xpaths": [
            ".//dc:references",
            ".//dc:URI",
            ".//gmd:distributionInfo//gmd:onLine//gmd:linkage//gmd:URL",
            ".//gmd:distributionInfo//gmd:MD_DigitalTransferOptions//gmd:onLine//gmd:URL"
        ]
    },
    {
        "name": "dominio",
        "type": "dominio",
        "domain_name": "Datos Espaciales",
        "domain_description": "Dominio general para datasets espaciales importados desde CSW"
    }
]
