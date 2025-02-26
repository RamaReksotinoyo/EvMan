# Event Management

This repo contains the system used to handle event management, I assume this is used for event organizer companies that have a field team in charge of being LO at an event.

Events that are handled here can have tracks, then within the tracks there are sessions. As an example, there is an event that is handled by an event organizer company, the event is called **Tech Confereence 2025**. In the event, there are tracks in it, then in the track there are sessions in the track. Here is the description:

- Event: Tech Conference 2025
  - Track: Frontend Development
    - Session: Modern React Patterns (10:00 - 11:30)
    - Session: Astro Best Practices (13:00 - 14:30)
    - Session: The power of vanila javascript (15:00 - 16:30)
  - Track: Backend Development
    - Session: Deep dive into goroutine golang (09:00 - 10:30)
    - Session: Why graphQL is bad (11:00 - 12:30)
    - Session: Database Optimization (14:00 - 15:30)
  - Track: DevOps & Cloud
    - Session: Docker & Kubernetes (09:30 - 11:00)
    - Session: AWS Solutions (13:00 - 14:30)
    - Session: CI/CD Pipeline Setup (15:00 - 16:30)

<br>

Later there are attendees who can register for this event, but the registered email cannot be registered again at the same event. 

Because everything in the event must be in order, so it is not allowed to collide or coincide with the session in the track, this is because the event organizer may have few employees, so only those who are only able to handle one track at a time. Likewise with events, whose times should not collide with each other. 

<br>

Here is the api documentation of the api management system:


|   Modul  |          API Url         | Method |   | Auth |
|:--------:|:------------------------:|:------:|:-:|:----:|
|   Event  |        /api/events       |   GET  |   |  Yes |
|          |     /api/events/{id}     |   GET  |   |  Yes |
|          |        /api/events       |  POST  |   |  Yes |
|          |     /api/events/{id}     |   PUT  |   |  Yes |
|          |     /api/events/{id}     | DELETE |   |  Yes |
|          |   /api/events/current    |   GET  |   |  No  |
|   Track  |        /api/tracks       |   GET  |   |  Yes |
|          |     /api/tracks/{id}     |   GET  |   |  Yes |
|          |        /api/tracks       |  POST  |   |  Yes |
|          |     /api/tracks/{id}     |   PUT  |   |  Yes |
|          |     /api/tracks/{id}     | DELETE |   |  Yes |
|  Session |       /api/sessions      |   GET  |   |  Yes |
|          |       /api/sessions      |  POST  |   |  Yes |
|          |    /api/sessions/{id}    |   GET  |   |  Yes |
|          |    /api/sessions/{id}    |   PUT  |   |  Yes |
|          |    /api/sessions/{id}    | DELETE |   |  Yes |
| Attendee |      /api/attendees      |   GET  |   |  Yes |
|          |      /api/attendees      |  POST  |   |  No  |
|          |    /api/attendees/{id}   |   GET  |   |  Yes |
|   Auth   |        /api/login        |  POST  |   |  No  |
|          |    /api/refresh-token    |  POST  |   |  Yes |

<br>
Most of the API access above requires logging in as a admin (django admin), or if in an event organizer company, it must be as someone holding an admin role in that company. There are several API endpoints that do not require admin authentication, which are:

<br>

- /api/login = This API is used for authenticated users to log in. The obtained token will be stored in the browser's HTTP-only cookies.
- /api/attendees (POST) = This API allows external users to register for an event without authentication, as long as they provide a valid email. (I imagine this working similarly to Google Forms).
- /api/events/current = This API allows external users to view events. for performance issues because this api is often hit by users, so I made it with raw query. And also here I give a rate limiter based on IP Address. 

<br>

Validate which events users are allowed to register for are located in /api/events/current. And because my assumption is that this is a small company, the events that are run are 1 by 1, no events can run simultaneously in the start_date and end_date time ranges. Then I also added that the next event that can be created is H+3 days after the end_date of the current event, this is used so that event organizer workers rest and prepare for the upcoming event.

<br>

Try it out:
```
docker-compose up -d
docker-compose exec django python manage.py migrate
docker-compose exec -it django python manage.py createsuperuser
```

The above steps are for running the application. During the creation process, the admin and password set at that time will be used to log in to the application or serve as the administrator for the event organizer company.

Next is running the tests. The tests for this application are located in the tests folder. There are three testing scopes in this application:

- Testing Django models = Tests the database's ability to handle and prevent unwanted data from being stored.
- Testing views/APIs = Tests the consistency of the APIs and business logic.
- Unit tests = Tests small functions individually, focusing on specific units or components.

How to run the tests:

```
docker-compose exec django python -Wd manage.py test core.tests -v 3
```


The results after the test was run were:
```
.......

----------------------------------------------------------------------
Ran 81 tests in 17.999s

OK
Destroying test database for alias 'default' ('test_evman')...
```

For API documentation, please see the URL **http://localhost:8001/api/docs/**

### Constrain
<br><br>
Konstrain pada database yang per

## Security & Reliability
<br>

#### HTTPOnly Cookie
Using tokens with the HttpOnly attribute is crucial for enhancing the security of web applications. Tokens stored in cookies with the HttpOnly attribute cannot be accessed by JavaScript running in the browser, thereby preventing Cross-Site Scripting (XSS) attacks that could exploit the token. In other words, if an attacker successfully injects malicious scripts into the application, they would not be able to steal the token because HttpOnly cookies cannot be read or modified by JavaScript. This provides an additional layer of security to protect sensitive user data, such as authentication tokens, from unauthorized access.
<br>

#### Rate Limiter
Rate limit by IP on core/utils/limit.py file will be used as decorators function, especially on unauthenticated endpoints, serves to limit the number of requests that can be made by an IP address in a given period of time. This prevents abuse or over-exploitation of the endpoint, such as brute force attacks, DDoS, or unreasonable use of server resources. By implementing rate limiting, to make ensure that every user or client has fair access to the endpoint, while maintaining overall system availability and performance. For example, if you set a limit of 100 requests per minute for each IP, users who exceed that limit will receive a 429 Too Many Requests response until a certain period of time passes. This helps protect the system from overloading and ensures stable service for all users.

#### Input sanitazion
Sanitizing user input is essential to prevent Cross-Site Scripting (XSS) attacks, which can allow attackers to inject malicious JavaScript into web applications. If input is not properly sanitized, it can lead to session hijacking, data theft, phishing attacks, or website defacement, compromising both user security and system integrity. Malicious scripts can steal sensitive data like cookies and authentication tokens, enabling unauthorized access. Additionally, uncontrolled JavaScript execution can manipulate the frontend and backend, affecting the application's behavior. By sanitizing input, developers protect users, maintain trust, and prevent security vulnerabilities, ensuring a safer and more reliable web experience. In this project the input sanitization function is placed in the folder core/utils/helpers.py. Which I implemented on the /api/attendees api (POST).







