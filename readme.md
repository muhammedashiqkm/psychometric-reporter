
````markdown
# Psychometric Portfolio & Employability Report Generator

This project is a FastAPI-based microservice that generates comprehensive **Employability Portfolios** for students. It fetches psychometric test data from a provided URL, analyzes it using an LLM (Gemini, OpenAI, or DeepSeek), generates visualizations (Charts), and compiles everything into a professional PDF report.

## 🚀 Features

* **External Data Fetching:** Accepts a `ProfileURL` to fetch student data dynamically.
* **Multi-Model AI Support:** Supports **Gemini**, **OpenAI**, and **DeepSeek** for generating employability insights.
* **Dynamic Visualizations:**
    * **Bar Charts:** Cognitive Ability (Category 2).
    * **Radar Charts:** Personality Traits (Category 1).
    * **Donut/Radial Charts:** Career Interests (Category 3).
    * **Seven Segment Charts:** Emotional Intelligence (Category 4).
    * **VARK Circles:** Learning Styles (Category 5).
    * **Variable Radius Charts:** Default fallback.
* **Parallel Processing:** Asynchronous execution of Main Analysis and VARK Analysis for high performance.
* **PDF Generation:** Uses `pdfkit` (wkhtmltopdf) and Jinja2 templates to create styled reports.

---

## 🛠️ API Documentation

### **Endpoint:** `POST /report/generate`

Generates the PDF report based on the student data found at the provided URL.

### **1. Request Format**

You do not send the full student data directly. Instead, you send the **URL** where the JSON data resides and the **AI Model** you wish to use.

**Headers:**
```http
Content-Type: application/json
Authorization: Bearer <your_token>
````

**Body:**

```json
{
  "model": "deepseek",
  "ProfileURL": "[http://127.0.0.1:5000/student.json](http://127.0.0.1:5000/student.json)"
}
```

| Field | Type | Options | Description |
| :--- | :--- | :--- | :--- |
| `model` | string | `gemini`, `openai`, `deepseek` | The LLM provider to use for analysis. |
| `ProfileURL` | string | Valid HTTP/HTTPS URL | The URL hosting the raw student JSON data. |

-----

### **2. Expected JSON Structure at `ProfileURL`**

The URL provided in the request must return a JSON object (or a list containing one object) matching this structure:

```json
[
  {
    "StudentName": "Priya S. Nair",
    "RegisterNo": "CS-2023-889",
    "CourseName": "B.Tech Computer Science",
    "InstitutionName": "Kerala Technical University",
    "Email": "priya.nair@example.com",
    "Batch": "2021 - 2025",
    "StudentPsychometricCategoryDetailsForPortfolioData": [
      {
        "KeyName": "first",
        "PsychometricTestCategory": "Technical Leadership",
        "JsonResult": "{\"sections\":[...], \"test_name\":\"Tech Lead Readiness\", \"description\":\"Evaluates readiness...\"}"
      },
      {
        "KeyName": "fifth",
        "PsychometricTestCategory": "Learning Modalities",
        "JsonResult": "{\"sections\":[...], \"test_name\":\"VARK Analysis\", \"description\":\"Determines learning preferences...\"}"
      }
    ]
  }
]
```

**Key Data Requirements:**

  * **`JsonResult`**: Must be a *stringified* JSON object containing `sections`, `test_name`, and `description`.
  * **`sections`**: A list of objects with `section`, `section_score`, and `interpretation`.

-----

### **3. Response Format**

On success, the API returns the filename and the downloadable URL of the generated PDF.

**Status Code:** `200 OK`

```json
{
  "filename": "Priya_S_Nair_Kerala_Technical_University_CS-2023-889.pdf",
  "report_url": "http://localhost:8000/media/reports/Priya_S_Nair_Kerala_Technical_University_CS-2023-889.pdf"
}
```


```
```