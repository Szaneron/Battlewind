# Battlewind - League of Legends Tournament Management Web Service

## Project description
The service was written in Python using one of the most popular frameworks for this language - Django. The website allows users to create their own teams, invite other users to join them, and offers these teams the opportunity to participate in a tournament. The application has its own image recognition module, which retrieves a screenshot uploaded by the user and decides which team advances further. It detects potential cheating attempts by editing the submitted image and actively participates in managing the tournament bracket. User profiles contain statistical data on their played matches, which are used to place users in appropriate positions in the website's ranking.

## Website functionalities
* Registration of users
* User login
* Viewing user profile
* Editing user profile
* Creating and editing teams by users
* Inviting users to join a team
* Accepting or rejecting invitations to a team by the invited user
* Removing users from a team
* Leaving a team by the user
* Viewing active tournaments by users
* Registering a team for a tournament
* Withdrawing from participating in a tournament before its start
* Uploading screenshots for analysis by the application after a match has ended
* Image recognition
* Viewing and managing user rankings on the website

## Main technologies used
Django - an open-source web application framework written in Python, which allows for rapid development of scalable and secure applications.
OpenCV - an open-source computer vision (CV) and image processing library, enabling analysis, manipulation, and pattern recognition in images and videos.
Pytesseract - a Python library for reading text from images and PDF files using Tesseract OCR.

## Implementation of the application
The logic of the application was implemented using Django and JavaScript technologies. /
The appearance of individual elements was set using the Bootstrap framework. /
The key functionality of the application is supported by the OpenCV and Pytesseract libraries./

## Image recognition module
The created module is designed to verify whether the uploaded image has undergone any graphic modifications and to extract the necessary data. To achieve this, two images are compared: the first one uploaded by the user and the second one stored in the application as a template. Then, fragments are cut out from both of these images, followed by pixel comparison through their color values contained in matrices. The cut-out fragments of each declared location are very similar to the text embedded in the image, with an accuracy of about 1 pixel. The cut-out fragments are relatively small, so during the comparison of the uploaded image fragment with the template, a difference of 1 pixel can exceed the allowable error margin of 1% of the compared fragment. The module is critical for the functionality of the application and utilizes OpenCV and Pytesseract libraries.
![image](https://user-images.githubusercontent.com/58951668/233054918-7a6d4d9e-fc5d-4d03-9327-b9f732ae7b6f.png)

## Tournament ladder management
The jQuery library is used for displaying and managing the tournament bracket. jQuery is a fast, small, and feature-rich JavaScript library. In the project, the jQuery Brackets library is used, which allows for creating and displaying various elimination brackets for tournament games. The data structure is not very complex, and information about the bracket is stored in a single object. The contents of this object determine what is rendered on the web page.
![image](https://user-images.githubusercontent.com/58951668/233055182-7bad9b2d-ec25-4c4d-9c5a-9dfb09be9fab.png)

## Testing
In the project, unit tests were created to test the logical part of the application. At the beginning, the "authenticatedUserTestCase" class was created, which contains tests checking the functionality of basic operations performed in the application.

## Service interface:
<details> 
<summary> Home screen </summary>
  
  ![image](https://user-images.githubusercontent.com/58951668/233055967-ae66bdca-f63e-4e40-8a7a-adfe7154d68c.png)
</details>

<details> 
<summary> User profile page </summary>
  
  ![image](https://user-images.githubusercontent.com/58951668/233056107-a6ce1df4-946a-4eb5-9c55-9676468d5755.png)
</details>

<details> 
<summary> Profile editing page </summary>
  
  ![image](https://user-images.githubusercontent.com/58951668/233056685-0f1a1527-e675-4aba-9824-174c2d50b732.png)
  ![image](https://user-images.githubusercontent.com/58951668/233056698-f6755c99-a4b2-41b8-b833-de1ee32e255a.png)
</details>

<details> 
<summary> Team details page </summary>
  
  ![image](https://user-images.githubusercontent.com/58951668/233056803-6ae5d87a-03f8-4c3b-96ed-fe867fcbd1c5.png)
</details>

<details> 
<summary> A page displaying the details of a specific tournament </summary>

  ![image](https://user-images.githubusercontent.com/58951668/233056233-78c8063e-91d1-44c2-badf-1e7768a4626d.png)
</details>

<details> 
<summary> A page displaying information about a specific match </summary>

  ![image](https://user-images.githubusercontent.com/58951668/233056362-4c25036e-fc75-4b3c-82ee-78b4b0e51bd3.png)
</details>

<details> 
<summary> Website presenting the ranking of users </summary>

  ![image](https://user-images.githubusercontent.com/58951668/233056454-96ecc038-b1fe-4a41-8134-6289f716edcb.png)
</details>

## Summary
Thanks to the minimalist and intuitive interface of the application, users can easily navigate the app, create their own accounts and teams, in which players compete together for victory in tournaments. The basic assumptions of the project have been met, the application allows users to participate in tournaments, collect statistical data based on played matches and place them in the ranking. The image recognition module is able to detect even the most precise editing and ensures the correct movement of teams in tournament brackets.
