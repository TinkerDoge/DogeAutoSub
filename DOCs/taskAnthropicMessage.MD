Proxy: Anthropic-Compatible
Anthropic-compatible proxy endpoints



POST
/proxy/anthropic/v1/messages
Create Messages


Parameters
Cancel
Reset
Name	Description
x-application-name
string | (string | null)
(header)
x-application-name
Request body

application/json
Edit Value
Schema
{
          "max_tokens": 1024,
          "messages": [
            {
              "content": "Hello, world",
              "role": "user"
            }
          ],
          "model": "claude-opus-4-6"
}
Execute
Clear
Responses
Curl

curl -X 'POST' \
  'https://mlaas.virtuosgames.com/proxy/anthropic/v1/messages' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJFNER4a3JGTWZYVW1hQkxnM2JUZGlGRXNUZFlEczFyNTlyTEpCUGNuWGpjIn0.eyJleHAiOjE3NzIxOTcyMjQsImlhdCI6MTc3MjE5MDAyNCwiYXV0aF90aW1lIjoxNzcyMTg2NjU5LCJqdGkiOiJvbnJ0YWM6YjllNjg0NWItNzFjNC1kNjdlLTMxY2UtMjg5Y2MxNDU2MGZlIiwiaXNzIjoiaHR0cHM6Ly9rY3Byby52aXJ0dW9zZ2FtZXMuY29tL3JlYWxtcy9WaXJ0dW9zIiwiYXVkIjpbIk1MQUFTLUNMSS1BUEkiLCJCVC1DTEktQVBJIiwiVkwtQ0xJLUFQSSIsImJyb2tlciIsImFjY291bnQiXSwic3ViIjoiNDgxZjMxZGItZDk5ZS00YmQyLThlMWUtMDIxOWFjM2M3YzNkIiwidHlwIjoiQmVhcmVyIiwiYXpwIjoiTUxBQVMtQ0xJLUFQSSIsInNpZCI6IjE3ZjVjMzQ5LTBkMmUtNGFmYS1iZTY1LTVhODE3ZTg0ZjM3ZSIsImFjciI6IjAiLCJhbGxvd2VkLW9yaWdpbnMiOlsiaHR0cHM6Ly9tbGFhcy52aXJ0dW9zZ2FtZXMuY29tIl0sInJlYWxtX2FjY2VzcyI6eyJyb2xlcyI6WyJkZWZhdWx0LXJvbGVzLXZpcnR1b3MiLCJvZmZsaW5lX2FjY2VzcyIsInVtYV9hdXRob3JpemF0aW9uIl19LCJyZXNvdXJjZV9hY2Nlc3MiOnsiQlQtQ0xJLUFQSSI6eyJyb2xlcyI6WyJCVC1ST0xFLUFETUlOLUMxMjExM1AyNjAwMV9UUklDWUNMRSIsIkJULVJPTEUtQURNSU4tQzExMDkwUDI0MDE3X0k0MCIsIkJULVJPTEUtQURNSU4tT1BSIiwiQlQtUk9MRS1FRElUT1ItU1VQQTA5MjQiLCJCVC1ST0xFLUFETUlOLURBSyIsIkJULVJPTEUtQURNSU4tQzIyMjg4UDI1MDAxX0tESCIsIkJULVJPTEUtQURNSU4tV09PS0lFRVNfV09OREVSRlVMX1dPUktTUEFDRSIsIkJULVJPTEUtQURNSU4tVlUuUEhBTUBWSVJUVU9TR0FNRVMuQ09NIiwiQlQtUk9MRS1FRElUT1ItU1VQQTA1MjUiLCJCVC1ST0xFLUVESVRPUi1DMjMxMzBQMjMwMDFfQ0FSUE9PTF8yMTEiLCJCVC1ST0xFLUlOVEFDQ0VTUyIsIkJULVJPTEUtQURNSU4tQklERElOR19ERUNLIiwiQlQtUk9MRS1FRElUT1ItQzIzMDI3UDIzMDAxX09UR19FTlYiLCJCVC1ST0xFLUVESVRPUi1TUEFSWF9MRVZFTF9BUlQiLCJCVC1ST0xFLUFETUlOLUMxMTA5MFAyNDAwMV9XT0xWRVJJTkVfSTM4Il19LCJNTEFBUy1DTEktQVBJIjp7InJvbGVzIjpbIk1MQUFTLVJPTEUtUkVHVUxBUiJdfSwiVkwtQ0xJLUFQSSI6eyJyb2xlcyI6WyJWTC1ST0xFLURPV05MT0FERVIiXX0sImJyb2tlciI6eyJyb2xlcyI6WyJyZWFkLXRva2VuIl19LCJhY2NvdW50Ijp7InJvbGVzIjpbIm1hbmFnZS1hY2NvdW50IiwibWFuYWdlLWFjY291bnQtbGlua3MiLCJ2aWV3LXByb2ZpbGUiXX19LCJzY29wZSI6Im9wZW5pZCBlbWFpbCBwcm9maWxlIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsIm5hbWUiOiJWdSBQaGFtIE5ndXllbiBEYW5nIiwicHJlZmVycmVkX3VzZXJuYW1lIjoidnUucGhhbUB2aXJ0dW9zZ2FtZXMuY29tIiwiZ2l2ZW5fbmFtZSI6IlZ1IiwiZmFtaWx5X25hbWUiOiJQaGFtIE5ndXllbiBEYW5nIiwiZW1haWwiOiJ2dS5waGFtQHZpcnR1b3Mtc3BhcnguY29tIn0.GI0aUt9aUe_wdsqqXI8NSpF0Wmzq9hV1XwBwYidG43aQ6hFEJZkyeyZMGwHJ5nCjPU4Y85ArdxrHsKTuhm8zL6Wihcgp3lVnbfgOI7KM-2Dp5ZN00OIVzc8EFBk7pqijNHgWQSohzZM9N6ew7JWQV45kAoHFe2rqwbncmz9_qInBqMIMCmufiHkggzQFVSMI3vRzJyjvMxUllu6mPGEBZNDy_uE24ZhhF27VD2PoqZc0XvQvsnb3t6hI-B-jq2ZHGiXiHz650-c_8wotsFIziQgxiX0eMJRMqny9KRQhMQY1T5gn94QCQsGSvKOg4ll3ceqHE4LpJ6ryR-1p_5ws5w' \
  -H 'Content-Type: application/json' \
  -d '{
          "max_tokens": 1024,
          "messages": [
            {
              "content": "Hello, world",
              "role": "user"
            }
          ],
          "model": "claude-opus-4-6"
}'
Request URL
https://mlaas.virtuosgames.com/proxy/anthropic/v1/messages
Server response
Code	Details
200	
Response body
Download
{
  "id": "msg_01VanPdc8SLcm6f4tRUsHf6C",
  "content": [
    {
      "citations": null,
      "text": "Hello! 👋 Welcome! How can I help you today? Whether you have questions, want to chat, or need assistance with something, I'm here for you. 😊",
      "type": "text"
    }
  ],
  "model": "claude-opus-4-6",
  "role": "assistant",
  "stop_reason": "end_turn",
  "stop_sequence": null,
  "type": "message",
  "usage": {
    "cache_creation": {
      "ephemeral_1h_input_tokens": 0,
      "ephemeral_5m_input_tokens": 0
    },
    "cache_creation_input_tokens": 0,
    "cache_read_input_tokens": 0,
    "inference_geo": "global",
    "input_tokens": 10,
    "output_tokens": 42,
    "server_tool_use": null,
    "service_tier": "standard"
  }
}
Response headers
 access-control-allow-credentials: true 
 content-length: 606 
 content-type: application/json 
 date: Fri,27 Feb 2026 12:05:55 GMT 
 server: uvicorn 
Responses
Code	Description	Links
200	
Messages created successfully.

Media type

application/json
Controls Accept header.
Example Value
Schema
"string"
No links
400	
Bad request. Invalid combination of request inputs/arguments.

Media type

application/json
Example Value
Schema
{
  "detail": "string"
}
No links
401	
Unauthorized. Authentication is required to access this route.

Media type

application/json
Example Value
Schema
{
  "detail": "string"
}
No links
403	
Forbidden. You are not authorized to access this route.

Media type

application/json
Example Value
Schema
{
  "detail": "string"
}
No links
410	
This endpoint is no longer available. The object detection service has been discontinued.

Media type

application/json
Example Value
Schema
{
  "detail": "string"
}
No links
422	
Validation Error

Media type

application/json
Example Value
Schema
{
  "detail": [
    {
      "loc": [
        "string",
        0
      ],
      "msg": "string",
      "type": "string",
      "input": "string",
      "ctx": {}
    }
  ]
}
No links
429	
Rate limit exceeded. Please try again later or extend limits.

Media type

application/json
Example Value
Schema
{
  "detail": "string"
}
No links
502	
Bad gateway. An upstream service is not responding or returned an invalid response.

Media type

application/json
Example Value
Schema
{
  "detail": "string"
}
No links
504	
Gateway timeout. An upstream service took too long to respond.

Media type

application/json
Example Value
Schema
{
  "detail": "string"
}
No links
