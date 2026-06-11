# API Documentation - mywebapp

This document defines the REST API endpoints provided by the **mywebapp** (Simple Inventory) service.

---

## 1. Business Logic Endpoints

### 1.1 Root Endpoint
* **Path**: `GET /`
* **Response Type**: `text/html`
* **Description**: Returns an HTML page listing all business logic endpoints.
* **Status Codes**: 
  * `200 OK`

---

### 1.2 Get All Items
* **Path**: `GET /items`
* **Response Formats**:
  * **JSON** (Default or when `Accept: application/json` is sent):
    * **Status Codes**: `200 OK`
    * **Response Body**:
      ```json
      [
        {
          "id": 1,
          "name": "Router Cisco 2911"
        },
        {
          "id": 2,
          "name": "Switch HP 2920"
        }
      ]
      ```
  * **HTML** (When `Accept: text/html` is sent):
    * **Status Codes**: `200 OK`
    * **Response Body**: A basic HTML document containing a table with columns `ID` and `Name`.

---

### 1.3 Create Item
* **Path**: `POST /items`
* **Headers**: `Content-Type: application/json`
* **Request Body**:
  ```json
  {
    "name": "Router Cisco 2911",
    "quantity": 5
  }
  ```
* **Response Format**: `application/json`
* **Status Codes**:
  * `201 Created`
  * `422 Unprocessable Entity` (Invalid JSON or schema validation error)
* **Response Body**:
  ```json
  {
    "id": 1,
    "name": "Router Cisco 2911",
    "quantity": 5
  }
  ```

---

### 1.4 Get Item Details
* **Path**: `GET /items/{id}`
* **Parameters**:
  * `id` (path, integer) - The unique identifier of the item.
* **Response Formats**:
  * **JSON** (Default or when `Accept: application/json` is sent):
    * **Status Codes**: 
      * `200 OK`
      * `404 Not Found` (Item does not exist)
    * **Response Body**:
      ```json
      {
        "id": 1,
        "name": "Router Cisco 2911",
        "quantity": 5,
        "created_at": "2026-06-11T12:00:00"
      }
      ```
  * **HTML** (When `Accept: text/html` is sent):
    * **Status Codes**: 
      * `200 OK`
      * `404 Not Found` (Item does not exist)
    * **Response Body**: A basic HTML document showing item attributes (ID, Name, Quantity, and Created At) inside a table.

---

## 2. System Endpoints

> [!WARNING]
> Access to these endpoints from outside is blocked by the Nginx reverse proxy configurations. They are only accessible from localhost (`127.0.0.1:5200`).

### 2.1 Liveness Probe
* **Path**: `GET /health/alive`
* **Response Type**: `text/plain`
* **Description**: Returns "OK" if the application is running.
* **Status Codes**:
  * `200 OK` ("OK")

---

### 2.2 Readiness Probe
* **Path**: `GET /health/ready`
* **Response Type**: `text/plain`
* **Description**: Checks database connectivity by executing `SELECT 1` in MariaDB.
* **Status Codes**:
  * `200 OK` ("Ready")
  * `500 Internal Server Error` (Database connection failed)
