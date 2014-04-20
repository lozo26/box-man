
def denseRanking(groups, setRank):
    """ '1223' ranking for four items A, B, C, D.
        If A ranks ahead of B and C (which compare equal) which are both ranked ahead of D,
        then A gets ranking number 1 ("first"), B gets ranking number 2 ("joint second"),
        C also gets ranking number 2 ("joint second") and D gets ranking number 3 ("third").
    """
    rank = 1
    for k, g in groups:
        for item in g:
            setRank(item, rank)
        rank += 1

def competitionRanking(groups, setRank):
    """ '1224' ranking for four items A, B, C, D.
        If A ranks ahead of B and C (which compare equal) which are both ranked ahead of D,
        then A gets ranking number 1 ("first"), B gets ranking number 2 ("joint second"),
        C also gets ranking number 2 ("joint second") and D gets ranking number 4 ("fourth").

        This ranking strategy is frequently adopted for competitions, as it means that if two (or more)
        competitors tie for a position in the ranking, the position of all those ranked below them is
        unaffected (i.e., a competitor only comes second if exactly one person scores better than them,
        third if exactly two people score better than them, fourth if exactly three people score better
        than them, etc.).
    """
    rank = 1
    for k, g in groups:
        cnt = 0
        for item in g:
            setRank(item, rank)
            cnt += 1
        rank += cnt

