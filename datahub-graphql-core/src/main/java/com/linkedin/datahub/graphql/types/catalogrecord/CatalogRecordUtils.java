package com.linkedin.datahub.graphql.types.catalogrecord;

import com.linkedin.common.urn.CatalogRecordUrn;
import com.linkedin.common.urn.DatasetUrn;

import java.net.URISyntaxException;

public class CatalogRecordUtils {

  private CatalogRecordUtils() {}

  static CatalogRecordUrn getCatalogRecordUrn(String urnStr) {
    try {
      return CatalogRecordUrn.createFromString(urnStr);
    } catch (URISyntaxException e) {
      throw new RuntimeException(
          String.format("Failed to retrieve dataset with urn %s, invalid urn", urnStr));
    }
  }
}
