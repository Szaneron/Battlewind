import cv2
import pytesseract
from django.shortcuts import get_object_or_404

from django.contrib import messages
from Website.models import *


def verify_iamge(request, match_id):
    match = get_object_or_404(Match, pk=match_id)

    # path to tesseract.exe
    pytesseract.pytesseract.tesseract_cmd = "C:\\Users\\Szane\\PycharmProjects\\Tessercat\\tesseract.exe"
    coreImagePath = r'Website/static'
    matchEndImagePath = str(match.afterGameImage.url)
    matchEndImagePath = coreImagePath + matchEndImagePath

    teamNamesObjects = [team for team in match.teamsInMatch.all()]
    print(teamNamesObjects)
    teamNamesList = [team.teamName for team in teamNamesObjects]
    print(teamNamesList)

    # Read end game summary image
    img_grey = cv2.imread(matchEndImagePath, 0)

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
        playerName = cv2.resize(img_grey[30:50, 1125:1280], (0, 0), fx=2, fy=2)
        playerNameValue = pytesseract.image_to_string(playerName)
        playerNameValue = playerNameValue.split("\n")
        playerNameValue = list(filter(None, playerNameValue))
        return playerNameValue[0]

    # Function that saves the summoner names of blue team players read from the picture to the list
    def get_summoner_names_for_team_blue_from_screen():
        playersName = cv2.resize(img_grey[155:360, 190:340], (0, 0), fx=2, fy=2)
        summonerNamesList = pytesseract.image_to_string(playersName)
        summonerNamesList = summonerNamesList.split("\n")
        summonerNamesList = [x.strip(' ') for x in summonerNamesList]
        summonerNamesList = list(filter(None, summonerNamesList))
        summonerNamesList = [x.lower() for x in summonerNamesList]
        summonerNamesList = [champName for champName in summonerNamesList if champName not in champList]
        return summonerNamesList

    # Function that saves the summoner names of red team players read from the picture to the list
    def get_summoner_names_for_team_red_from_screen():
        playersName = cv2.resize(img_grey[395:600, 190:340], (0, 0), fx=2, fy=2)
        summonerNamesList = pytesseract.image_to_string(playersName)
        summonerNamesList = summonerNamesList.split("\n")
        summonerNamesList = [x.strip(' ') for x in summonerNamesList]
        summonerNamesList = list(filter(None, summonerNamesList))
        summonerNamesList = [x.lower() for x in summonerNamesList]
        summonerNamesList = [champName for champName in summonerNamesList if champName not in champList]
        return summonerNamesList

    # Function that reads whether the game on the screen was won or lost
    def get_game_end_status():
        screenGameStatus = cv2.resize(img_grey[15:45, 70:200], (0, 0), fx=2, fy=2)
        screenGameStatus = pytesseract.image_to_string(screenGameStatus)
        screenGameStatus = screenGameStatus.split("\n")
        screenGameStatus = list(filter(None, screenGameStatus))
        return screenGameStatus

    # function that checks if summoner names from the screenshot are the same as the summoner names from the database
    def validate_summoner_names(siteList, screenList):
        siteList.sort()
        screenList.sort()
        numberOfCorrectPlayers = 0
        try:
            for iterator in range(5):
                if siteList[iterator] == screenList[iterator]:
                    numberOfCorrectPlayers += 1
        except:
            messages.error(request,
                           'Problem z listą podczas validacji nazw przywoływaczy. Prześlij ponownie zrzut ekranu!')

        if numberOfCorrectPlayers >= 3:
            return numberOfCorrectPlayers
        else:
            return messages.error("Błąd weryfikacji - Ilośc poprwanie wykrytych:", numberOfCorrectPlayers)

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

    # Team Red summoner names list from db
    redTeamSummonerNameList = get_red_team_summoner_names_list()
    redTeamSummonerNameListLower = [x.lower() for x in redTeamSummonerNameList]

    # Summoner name read from screen that send the eng game image
    screenSenderSummonerName = get_screen_sender_summoner_name()
    screenSenderSummonerNameLower = screenSenderSummonerName.lower()

    # Site user-object of user that send the end game image
    userThatSendImage = User.objects.get(profile__summonerName=screenSenderSummonerName)

    # Summoner names read from the image for team blue
    screenTeamBlueSummonerNames = get_summoner_names_for_team_blue_from_screen()
    # Summoner names read from the image for team red
    screenTeamRedSummonerNames = get_summoner_names_for_team_red_from_screen()

    validationResultForTeamBlue = validate_summoner_names(blueTeamSummonerNameListLower, screenTeamBlueSummonerNames)
    validationResultForTeamRed = validate_summoner_names(redTeamSummonerNameListLower, screenTeamRedSummonerNames)

    endGameStatus = get_game_end_status()

    if validationResultForTeamBlue >= 3 and validationResultForTeamRed >= 3:
        winnerTeam = get_winner_team(screenTeamBlueSummonerNames, screenTeamRedSummonerNames,
                                     screenSenderSummonerNameLower,
                                     endGameStatus)
        
    return winnerTeam

################################################################################
#
# def verify_key_points_of_image():
#     keyOne = cv2.resize(img_color[355:400, 390:1050], (0, 0), fx=1, fy=1)
#
#     # keyTwo = cv2.resize(img_color[80:655, 650:710], (0, 0), fx=1, fy=1)
#     keyTwoT = cv2.resize(img_template[80:655, 650:710], (0, 0), fx=1.2, fy=1.2)
#     keyTwo = cv2.resize(img_grey[395:600, 190:340], (0, 0), fx=2, fy=2)
#     result = cv2.matchTemplate(img_color, key2, cv2.TM_SQDIFF_NORMED)
#     min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
#     if min_loc == (0, 0) and max_loc == (4, 5):
#         print("MATCH")
#     else:
#         print("NOT MATCH")
#     found = (min_loc, max_loc)
#     print(found)
#     if cv2.TM_CCOEFF_NORMED in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
#         location = min_loc
#     else:
#         location = max_loc
#
#     bottom_right = (location[0] + w, location[1] + h)
#     cv2.rectangle(img_color, location, bottom_right, 255, 5)
#     cv2.imshow('Match', img_color)
#     cv2.waitKey(0)
#     cv2.destroyAllWindows()
