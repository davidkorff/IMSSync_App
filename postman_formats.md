# Postman SOAP Request Formats for IMS DataAccess

## Setup in Postman
- **URL**: `https://webservices.mgasystems.com/ims_demo/Dataaccess.asmx`
- **Method**: POST
- **Headers**:
  - `Content-Type`: `text/xml; charset=utf-8`
  - `SOAPAction`: `"http://tempuri.org/IMSWebServices/DataAccess/ExecuteDataSet"`

## Format 1: Basic (What we're currently sending)
```xml
<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Header>
    <TokenHeader xmlns="http://tempuri.org/IMSWebServices/DataAccess">
      <Token>fb01e05b-fbc3-467c-bd25-7163c63080a4</Token>
      <Context>RSG</Context>
    </TokenHeader>
  </soap:Header>
  <soap:Body>
    <ExecuteDataSet xmlns="http://tempuri.org/IMSWebServices/DataAccess">
      <procedureName>spGetQuoteOptions</procedureName>
      <parameters>
        <string>QuoteGuid</string>
        <string>f57495b2-425c-4f07-a115-ccd5beedd5e4</string>
      </parameters>
    </ExecuteDataSet>
  </soap:Body>
</soap:Envelope>
```

## Format 2: With @ Prefix
```xml
<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Header>
    <TokenHeader xmlns="http://tempuri.org/IMSWebServices/DataAccess">
      <Token>fb01e05b-fbc3-467c-bd25-7163c63080a4</Token>
      <Context>RSG</Context>
    </TokenHeader>
  </soap:Header>
  <soap:Body>
    <ExecuteDataSet xmlns="http://tempuri.org/IMSWebServices/DataAccess">
      <procedureName>spGetQuoteOptions</procedureName>
      <parameters>
        <string>@QuoteGuid</string>
        <string>f57495b2-425c-4f07-a115-ccd5beedd5e4</string>
      </parameters>
    </ExecuteDataSet>
  </soap:Body>
</soap:Envelope>
```

## Format 3: Key=Value Format
```xml
<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Header>
    <TokenHeader xmlns="http://tempuri.org/IMSWebServices/DataAccess">
      <Token>fb01e05b-fbc3-467c-bd25-7163c63080a4</Token>
      <Context>RSG</Context>
    </TokenHeader>
  </soap:Header>
  <soap:Body>
    <ExecuteDataSet xmlns="http://tempuri.org/IMSWebServices/DataAccess">
      <procedureName>spGetQuoteOptions</procedureName>
      <parameters>
        <string>QuoteGuid=f57495b2-425c-4f07-a115-ccd5beedd5e4</string>
      </parameters>
    </ExecuteDataSet>
  </soap:Body>
</soap:Envelope>
```

## Format 4: Alternative Key/Value Pairs
```xml
<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Header>
    <TokenHeader xmlns="http://tempuri.org/IMSWebServices/DataAccess">
      <Token>fb01e05b-fbc3-467c-bd25-7163c63080a4</Token>
      <Context>RSG</Context>
    </TokenHeader>
  </soap:Header>
  <soap:Body>
    <ExecuteDataSet xmlns="http://tempuri.org/IMSWebServices/DataAccess">
      <procedureName>spGetQuoteOptions</procedureName>
      <parameters>
        <string>@QuoteGuid=f57495b2-425c-4f07-a115-ccd5beedd5e4</string>
      </parameters>
    </ExecuteDataSet>
  </soap:Body>
</soap:Envelope>
```

## What is QuoteOptionID?

Based on the logs and IMS structure:

1. **QuoteOptionGUID** (e.g., `52f3fa37-779b-4e39-adde-6bcbcadbaa26`): This is what `AddQuoteOption` returns - a GUID identifier
2. **QuoteOptionID** (integer, e.g., `613649`): This is the database integer primary key that the Bind methods need

The problem is:
- `AddQuoteOption` returns a GUID
- `Bind(quoteOptionID)` needs an integer ID
- We need `spGetQuoteOptions_WS` to map between them

From your logs, we can see:
- Quote GUID: `f57495b2-425c-4f07-a115-ccd5beedd5e4`
- Quote ID (integer): `613649` (extracted from error)
- Quote Option GUID: `52f3fa37-779b-4e39-adde-6bcbcadbaa26` (returned by AddQuoteOption)
- Quote Option ID: Unknown (this is what we need!)

## Test Instructions

1. Copy each format above
2. In Postman:
   - Set method to POST
   - Set URL to your IMS endpoint
   - Add headers as shown above
   - Paste the XML in the Body (raw)
   - Send the request

3. If one works, note which format and we'll update the code accordingly
4. The response should contain the QuoteOptionID we need for binding