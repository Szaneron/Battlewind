import cv2
import numpy as np
import pytesseract
from django.contrib import messages
from django.shortcuts import get_object_or_404

from Website.models import *


def verify_iamge(request, match_id):
    match = get_object_or_404(Match, pk=match_id)

    # path to tesseract.exe
    pytesseract.pytesseract.tesseract_cmd = "C:\\Users\\Armin\\PycharmProjects\\Tessercat\\tesseract.exe"
    coreImagePath = r'Website/static'
    matchEndImagePath = str(match.afterGameImage.url)
    matchEndImagePath = coreImagePath + matchEndImagePath

    teamNamesObjects = [team for team in match.teamsInMatch.all()]
    teamNamesList = [team.teamName for team in teamNamesObjects]

    # Read end game summary image
    img_grey = cv2.imread(matchEndImagePath, 0)
    img_color = cv2.imread(matchEndImagePath, 1)
    img_template = cv2.imread(r'Website/static/mecz_template.png', 1)

    # Function that checks key areas of the image for edits
    def verify_key_points_of_image():
        # Key for middle horizontal space
        keyOneImage = cv2.resize(img_color[355:400, 390:1050], (0, 0), fx=1, fy=1)
        keyOneTemplate = cv2.resize(img_template[355:400, 390:1050], (0, 0), fx=1, fy=1)

        # Keys for Victory/Defeat
        keyTwoImageTop = cv2.resize(img_color[15:22, 70:200], (0, 0), fx=1, fy=1)
        keyTwoTemplateTop = cv2.resize(img_template[15:22, 70:200], (0, 0), fx=1, fy=1)
        keyTwoImageBottom = cv2.resize(img_color[39:48, 70:200], (0, 0), fx=1, fy=1)
        keyTwoTemplateBottom = cv2.resize(img_template[39:48, 70:200], (0, 0), fx=1, fy=1)
        keyThreeImage = cv2.resize(img_color[15:45, 70:78], (0, 0), fx=1, fy=1)
        keyThreeTemplate = cv2.resize(img_template[15:45, 70:78], (0, 0), fx=1, fy=1)

        # Keys for first team players change
        keyFourImagePlayer1 = cv2.resize(img_color[155:161, 230:340], (0, 0), fx=1, fy=1)
        keyFourTemplatePlayer1 = cv2.resize(img_template[155:161, 230:340], (0, 0), fx=1, fy=1)
        keyFourImagePlayer2 = cv2.resize(img_color[195:201, 230:340], (0, 0), fx=1, fy=1)
        keyFourTemplatePlayer2 = cv2.resize(img_template[195:201, 230:340], (0, 0), fx=1, fy=1)
        keyFourImagePlayer3 = cv2.resize(img_color[236:243, 230:340], (0, 0), fx=1, fy=1)
        keyFourTemplatePlayer3 = cv2.resize(img_template[236:243, 230:340], (0, 0), fx=1, fy=1)

        # Keys for second team players change
        keyFourImagePlayer4 = cv2.resize(img_color[395:403, 230:340], (0, 0), fx=1, fy=1)
        keyFourTemplatePlayer4 = cv2.resize(img_template[395:403, 230:340], (0, 0), fx=1, fy=1)
        keyFourImagePlayer5 = cv2.resize(img_color[437:444, 230:340], (0, 0), fx=1, fy=1)
        keyFourTemplatePlayer5 = cv2.resize(img_template[437:444, 230:340], (0, 0), fx=1, fy=1)
        keyFourImagePlayer6 = cv2.resize(img_color[477:485, 230:340], (0, 0), fx=1, fy=1)
        keyFourTemplatePlayer6 = cv2.resize(img_template[477:485, 230:340], (0, 0), fx=1, fy=1)

        # Key for middle vertical space
        keyFiveImage = cv2.resize(img_color[100:630, 650:715], (0, 0), fx=1, fy=1)
        keyFiveTemplate = cv2.resize(img_template[100:630, 650:715], (0, 0), fx=1, fy=1)

        # Key for summoner name
        keySixImage1 = cv2.resize(img_color[29:34, 1151:1320], (0, 0), fx=1, fy=1)
        keySixTemplate1 = cv2.resize(img_template[29:34, 1151:1320], (0, 0), fx=1, fy=1)
        keySixImage2 = cv2.resize(img_color[37:50, 1127:1135], (0, 0), fx=1, fy=1)
        keySixTemplate2 = cv2.resize(img_template[37:50, 1127:1135], (0, 0), fx=1, fy=1)

        # Function that calculates the percentage difference between the uploaded image and the template
        def get_diff(image, template):
            result = cv2.absdiff(image, template)
            result = result.astype(np.uint8)
            percentage = (np.count_nonzero(result) * 100) / result.size
            return percentage

        resultOne = get_diff(keyOneImage, keyOneTemplate)
        print('resultOne: ', resultOne)
        resultTwo1 = get_diff(keyTwoImageTop, keyTwoTemplateTop)
        print('resultTwo1: ', resultTwo1)
        resultTwo2 = get_diff(keyTwoImageBottom, keyTwoTemplateBottom)
        print('resultTwo2: ', resultTwo2)
        resultThree = get_diff(keyThreeImage, keyThreeTemplate)
        print('resultThree: ', resultThree)
        resultFourP1 = get_diff(keyFourImagePlayer1, keyFourTemplatePlayer1)
        print('resultFourP1: ', resultFourP1)
        resultFourP2 = get_diff(keyFourImagePlayer2, keyFourTemplatePlayer2)
        print('resultFourP2: ', resultFourP2)
        resultFourP3 = get_diff(keyFourImagePlayer3, keyFourTemplatePlayer3)
        print('resultFourP3: ', resultFourP3)
        resultFourP4 = get_diff(keyFourImagePlayer4, keyFourTemplatePlayer4)
        print('resultFourP4: ', resultFourP4)
        resultFourP5 = get_diff(keyFourImagePlayer5, keyFourTemplatePlayer5)
        print('resultFourP5: ', resultFourP5)
        resultFourP6 = get_diff(keyFourImagePlayer6, keyFourTemplatePlayer6)
        print('resultFourP6: ', resultFourP6)
        resultFive = get_diff(keyFiveImage, keyFiveTemplate)
        print('resultFive: ', resultFive)
        resultSix1 = get_diff(keySixImage1, keySixTemplate1)
        print('resultSix1: ', resultSix1)
        resultSix2 = get_diff(keySixImage2, keySixTemplate2)
        print('resultSix2: ', resultSix2)

        if resultOne < 1 and resultTwo1 < 1 and resultTwo2 < 1 and resultThree < 1 and resultFourP1 < 1 and resultFourP2 < 1 and resultFourP3 < 1 and resultFourP4 < 1 and resultFourP5 < 1 and resultFourP6 < 1 and resultFive < 1 and resultSix1 < 1 and resultSix2 < 1:
            return True
        else:
            return False

    # Function that fetches summoner names for team Blue from the database and saves them to the list
    def get_blue_team_summoner_names_list():
        blueTeamSummonerNameList = []
        blueUsers = User.objects.filter(teams__teamName=teamNamesList[0])
        for user in blueUsers:
            blueTeamSummonerNameList.append(user.profile.summonerName)
        return blueTeamSummonerNameList

    # Function that fetches summoner names for team Red from the database and saves them to the list
    def get_red_team_summoner_names_list():
        redTeamSummonerNameList = []
        redUsers = User.objects.filter(teams__teamName=teamNamesList[1])
        for user in redUsers:
            redTeamSummonerNameList.append(user.profile.summonerName)
        return redTeamSummonerNameList

    # Function that downloads and saves existing characters in the game to the list
    def get_dictionary_champion_list():
        # with context manager assures us the
        # file will be closed when leaving the scope
        with open('Website/static/champions.txt') as file:
            # return the split results, which is all the words in the file.
            return [line.rstrip('\n') for line in file]

    # Function that checks the Summoner Name logged into the client
    def get_screen_sender_summoner_name():
        playerName = cv2.resize(img_grey[25:52, 1125:1280], (0, 0), fx=1.8, fy=1.8)
        playerNameValue = pytesseract.image_to_string(playerName)
        playerNameValue = playerNameValue.split("\n")
        playerNameValue = list(filter(None, playerNameValue))
        return playerNameValue[0]

    # Function that saves the summoner names of blue team players read from the picture to the list
    def get_summoner_names_for_team_one_from_screen():
        playersName = cv2.resize(img_grey[155:360, 190:340], (0, 0), fx=1.8, fy=1.8)
        summonerNamesList = pytesseract.image_to_string(playersName)
        summonerNamesList = summonerNamesList.split("\n")
        summonerNamesList = [x.strip(' ') for x in summonerNamesList]
        summonerNamesList = list(filter(None, summonerNamesList))
        summonerNamesList = [x.lower() for x in summonerNamesList]
        summonerNamesList = [champName for champName in summonerNamesList if champName not in champList]
        return summonerNamesList

    # Function that saves the summoner names of red team players read from the picture to the list
    def get_summoner_names_for_team_two_from_screen():
        playersName = cv2.resize(img_grey[395:600, 190:340], (0, 0), fx=1.8, fy=1.8)
        summonerNamesList = pytesseract.image_to_string(playersName)
        summonerNamesList = summonerNamesList.split("\n")
        summonerNamesList = [x.strip(' ') for x in summonerNamesList]
        summonerNamesList = list(filter(None, summonerNamesList))
        summonerNamesList = [x.lower() for x in summonerNamesList]
        summonerNamesList = [champName for champName in summonerNamesList if champName not in champList]
        return summonerNamesList

    # Function that assigns the summoner names taken from the screenshot to the matching teams from the base
    def assign_screen_summoner_names_to_teams(blueTeamDb, oneTeamScreen, redTeamDb, twoTeamScreen):
        blueTeamDb = set(blueTeamDb)
        oneTeamScreen = set(oneTeamScreen)
        redTeamDb = set(redTeamDb)
        twoTeamScreen = set(twoTeamScreen)
        colorTeamList = []

        validationOne = blueTeamDb.intersection(oneTeamScreen)
        validationTwo = redTeamDb.intersection(twoTeamScreen)
        if len(validationOne) >= 3 and len(validationTwo) >= 3:
            colorTeamList.append(oneTeamScreen)
            colorTeamList.append(twoTeamScreen)
        else:
            colorTeamList.append(twoTeamScreen)
            colorTeamList.append(oneTeamScreen)

        return colorTeamList

    # Function that reads whether the game on the screen was won or lost
    def get_game_end_status():
        screenGameStatus = cv2.resize(img_grey[15:45, 70:200], (0, 0), fx=2, fy=2)
        screenGameStatus = pytesseract.image_to_string(screenGameStatus)
        screenGameStatus = screenGameStatus.split("\n")
        screenGameStatus = list(filter(None, screenGameStatus))
        return screenGameStatus

    # function that checks if summoner names from the screenshot are the same as the summoner names from the database
    def validate_summoner_names(siteList, screenList):
        setSiteList = set(siteList)
        setScreenlist = set(screenList)

        validation = setSiteList.intersection(setScreenlist)

        if len(validation) >= 3:
            return len(validation)

    # Function that selects the winning team
    def get_winner_team(blueTeam, redTeam, summonerName, gameStatus):
        if summonerName in blueTeam and gameStatus[0] == "VICTORY":
            return teamNamesList[0]
        elif summonerName in redTeam and gameStatus[0] == "VICTORY":
            return teamNamesList[1]
        elif summonerName in blueTeam and gameStatus[0] == "DEFEAT":
            return teamNamesList[1]
        elif summonerName in redTeam and gameStatus[0] == "DEFEAT":
            return teamNamesList[0]
        else:
            messages.error(request, 'Nie rozpoznano zwycięskiej drużyny')

    # List of champions that exists in Game
    champList = get_dictionary_champion_list()
    champList = [x.lower() for x in champList]

    # Team Blue summoner names list from db
    blueTeamSummonerNameList = get_blue_team_summoner_names_list()
    blueTeamSummonerNameListLower = [x.lower() for x in blueTeamSummonerNameList]
    print('bluedb:', blueTeamSummonerNameListLower)

    # Team Red summoner names list from db
    redTeamSummonerNameList = get_red_team_summoner_names_list()
    redTeamSummonerNameListLower = [x.lower() for x in redTeamSummonerNameList]
    print('reddb', redTeamSummonerNameListLower)

    # Summoner name read from screen that send the eng game image
    screenSenderSummonerName = get_screen_sender_summoner_name()
    screenSenderSummonerNameLower = screenSenderSummonerName.lower()
    print(screenSenderSummonerNameLower)

    # Summoner names read from the image for team one
    screenTeamOneSummonerNames = get_summoner_names_for_team_one_from_screen()
    print('bluecreen', screenTeamOneSummonerNames)
    # Summoner names read from the image for team two
    screenTeamTwoSummonerNames = get_summoner_names_for_team_two_from_screen()
    print('redscreen', screenTeamTwoSummonerNames)

    assignedTeamColorList = assign_screen_summoner_names_to_teams(blueTeamSummonerNameListLower,
                                                                  screenTeamOneSummonerNames,
                                                                  redTeamSummonerNameListLower,
                                                                  screenTeamTwoSummonerNames)

    screenTeamBlueSummonerNames = assignedTeamColorList[0]
    screenTeamRedSummonerNames = assignedTeamColorList[1]

    validationResultForTeamBlue = validate_summoner_names(blueTeamSummonerNameListLower,
                                                          screenTeamBlueSummonerNames)
    print(validationResultForTeamBlue)
    validationResultForTeamRed = validate_summoner_names(redTeamSummonerNameListLower, screenTeamRedSummonerNames)
    print(validationResultForTeamRed)

    endGameStatus = get_game_end_status()
    print(endGameStatus)

    if validationResultForTeamBlue >= 3 and validationResultForTeamRed >= 3:
        if verify_key_points_of_image():
            winnerTeam = get_winner_team(blueTeamSummonerNameListLower, redTeamSummonerNameListLower,
                                         screenSenderSummonerNameLower, endGameStatus)
            return winnerTeam
        else:
            return 0
