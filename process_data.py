from __future__ import division

import pandas as pd
import seaborn as sns
import scipy.stats
from matplotlib import pyplot as plt

data_raw = pd.read_csv('data.csv')

renames = {
    ### Good Ventures
    'Suppose that, over the time period the match was active, GiveDirectly raised >>>$4.5 million.<<< If you had donated $10 to GiveDirectly at that time, how much MORE MONEY would they have received than if you had not donated anything? (This includes both money that you donated, and money that Good Ventures donated that would otherwise not have been donated.)': 'GV_cf_match',
    'Suppose that, over the time period the match was active, GiveDirectly raised >>>$5.1 million.<<< If you had donated $10 to GiveDirectly at that time, how much MORE MONEY would they have received than if you had not donated anything? (This includes both money that you donated, and money that Good Ventures donated that would otherwise not have been donated.)': 'GV_cf_nomatch',
    'How much would you donate, if GiveDirectly had raised >>>$4.5 million<<< that was eligible for the match?': 'GV_donation_match',
    'How much would you donate, if GiveDirectly had raised >>>$5.1 million<<< that was eligible for the match?': 'GV_donation_nomatch',
    'How much would you donate, if GiveDirectly had raised >>>$5.1 million<<< in response to the challenge?': 'GV_donation_nochallenge',
    'How much would you donate, if GiveDirectly had raised >>>$4.5 million<<< in response to the challenge?': 'GV_donation_challenge',
    'I perceive Good Ventures as...': 'GV_honest',
    'My level of familiarity with Good Ventures is...': 'GV_familiar',

    ### HEA
    "Suppose that, over the time period the match was active, HEA raised >>>$4,500.<<< If you had donated $10 to the fundraiser at that time, how much MORE MONEY do you think GiveWell's top charities would have received, than if you had not donated anything? (This includes both money that you donated, and money that HEA's anonymous donor donated that would otherwise not have been donated.)": 'HEA_cf_match',
    "Suppose that, over the time period the match was active, HEA raised >>>$5,100.<<< If you had donated $10 to the fundraiser at that time, how much MORE MONEY do you think GiveWell's top charities would have received, than if you had not donated anything? (This includes both money that you donated, and money that HEA's anonymous donor donated that would otherwise not have been donated.)": 'HEA_cf_nomatch',
    'How much would you donate, if HEA had raised >>>$4,500<<< that was eligible for the match?': 'HEA_donation_match',
    'How much would you donate, if HEA had raised >>>$5,100<<< that was eligible for the match?': 'HEA_donation_nomatch',
    'How much would you donate, if HEA had raised >>>$4,500<<< in response to the challenge?': 'HEA_donation_challenge',
    'How much would you donate, if HEA had raised >>>$5,100<<< in response to the challenge?': 'HEA_donation_nochallenge',
    'I would describe HEA as...': 'HEA_honest',
    'My level of familiarity with HEA is...': 'HEA_familiar',

    ### Friend
    'Suppose that, over the time period the match was active, your friend raised >>>$4,500.<<< If you had donated $10 to the fundraiser at that time, how much MORE MONEY do you think Cute Puppies for Orphans would have received, than if you had not donated anything? (This includes both money that you donated, and money that your friend donated that would otherwise not have been donated.)': 'friend_cf_match',
    'Suppose that, over the time period the match was active, your friend raised >>>$5,100.<<< If you had donated $10 to the fundraiser at that time, how much MORE MONEY do you think Cute Puppies for Orphans would have received, than if you had not donated anything? (This includes both money that you donated, and money that your friend donated that would otherwise not have been donated.)': 'friend_cf_nomatch',
    'How much would you donate, if your friend had raised >>>$4,500<<< that was eligible for the match?': 'friend_donation_match',
    'How much would you donate, if your friend had raised >>>$4,500<<< in response to the challenge?': 'friend_donation_challenge',
    'How much would you donate, if your friend had raised >>>$5,100<<< in response to the challenge?': 'friend_donation_nochallenge',
    'How much would you donate, if your friend had raised >>>$5,100<<< that was eligible for the match?': 'friend_donation_nomatch',
    "I would describe the friend I'm thinking of as...": 'friend_honest',

    ### Demographics
    'How familiar are you with effective altruism?': 'demog_EA',
    'How familiar are you with charity fundraisers?': 'demog_charity',
    'How familiar are you with the idea of a counterfactual, or counterfactual reasoning?': 'demog_cf',
    'How familiar are you with the idea of utilitarianism?': 'demog_util',
    'If I learned that funds put up for a matching campaign would be donated regardless of whether the match was fulfilled--for instance, that Good Ventures would have given $5 million to GiveDirectly even if they had raised only $4 million from the public--I would feel...': 'demog_deceived'
}

data_dirty = data_raw[renames.keys()].rename(columns=renames)

ORGS_AND_NAMES = [
    ('GV', 'Good Ventures'),
    ('HEA', 'Harvard Effective Altruism'),
    ('friend', 'Friend'),
]
ORG_NAMES = zip(*ORGS_AND_NAMES)[1]
ORG_COLUMNS = ['cf_match', 'cf_nomatch', 'donation_match', 'donation_nomatch',
               'donation_challenge', 'donation_nochallenge', 'honest']

### Clean up the data

data = data_dirty.copy()
mask = pd.Series(False, index=data.index)
for org, name in ORGS_AND_NAMES:
    # remove people who thought GD got more $ from additional donations after the match finished
    cf_match = data['%s_cf_match' % org]
    cf_nomatch = data['%s_cf_nomatch' % org]
    diff = cf_match - cf_nomatch
    weird = (diff < 0)
    print "{n} people thought {name} got more money after match was finished".format(
        n=weird.sum(), name=name)
    mask |= weird

    weird2 = ((data['%s_donation_match' % org] < 0)
              | (data['%s_donation_nomatch' % org] < 0)
              | (data['%s_donation_challenge' % org] < 0)
              | (data['%s_donation_nochallenge' % org] < 0))
    print "{n} people gave at least one gift < 0 to {name}".format(
        n=weird2.sum(), name=name)


data = data[~mask]
print len(data), "samples remaining"

### "Melted" dfs for Seaborn. We make one for cf, one for match gift, and one for challenge gift

AMOUNT = 'Gift size'
MATCHER = 'Matcher'
LIMIT = 'Below limit'

def get_melted_data(col_below_limit, col_above_limit):
    meltedcols = [MATCHER, LIMIT, AMOUNT]
    data_melted = pd.DataFrame(columns=meltedcols, index=[])
    for org, name in ORGS_AND_NAMES:
        melty_below = pd.DataFrame({AMOUNT: data['%s_%s' % (org, col_below_limit)],
                                    MATCHER: name, LIMIT:'Yes'})
        melty_above = pd.DataFrame({AMOUNT: data['%s_%s' % (org, col_above_limit)],
                                    MATCHER: name, LIMIT:'No'})
        data_melted = pd.concat([data_melted, melty_below, melty_above])
    return data_melted

data_melted_match = get_melted_data('donation_match', 'donation_nomatch')

data_melted_challenge = get_melted_data('donation_challenge', 'donation_nochallenge')

# compare unmet match to unmet challenge
data_melted_mvsc = get_melted_data('donation_match', 'donation_challenge').rename(
    columns={LIMIT:'type'})
data_melted_mvsc['type'] = data_melted_mvsc['type'].apply({'Yes': 'Match', 'No': 'Challenge'}.get)

### How much money do people think the matcher gives, counterfactually adjusted?

def plot_h1():
    FULL = 'Full amount'
    SOME = 'Partial amount'
    NONE = 'Nothing'
    df = pd.DataFrame(columns=[FULL, SOME, NONE], index=ORG_NAMES)
    for org, name in ORGS_AND_NAMES:
        cf_match = data['%s_cf_match' % org]
        cf_nomatch = data['%s_cf_nomatch' % org]
        diff = cf_match - cf_nomatch
        full = (diff >= 10).sum()
        some = ((diff < 10) & (diff > 0)).sum()
        none = (diff == 0).sum()
        less = (diff < 0).sum()
        assert less == 0
        assert full + some + none == len(diff)
        df.loc[name, FULL] = full
        df.loc[name, SOME] = some
        df.loc[name, NONE] = none
    # TODO confidence intervals
    title = "How much did the matcher donate, counterfactually adjusted?"
    g = df.plot(kind='bar', stacked=True, ylim=[0,len(diff)], rot=0, title=title)

### How many people want to give more during matches?

def plot_h2():
    g = sns.factorplot(MATCHER, AMOUNT, LIMIT, hue_order=('Yes', 'No'),
                       data=data_melted_match, kind='bar', x_order=ORG_NAMES)
    plt.title("Average donation to a match campaign")

def plot_h2_2():
    f, ax = plt.subplots(1, 3, sharey=True)
    for i, (org, name) in enumerate(ORGS_AND_NAMES):
        yes = data[org+'_donation_match']
        no = data[org+'_donation_nomatch']
        zero = (yes == 0)
        yes = yes[~zero]
        no = no[~zero]
        YES = 'Below limit'
        NO = 'Above limit'
        df = pd.DataFrame({ YES: yes, NO: no })[[YES, NO]]
        diff = (no - yes).mean()
        t, pval = scipy.stats.ttest_1samp((no - yes), 0)
        sns.violinplot(df, inner='box', join_rm=True, ax=ax[i])
        avg = yes.mean()
        ax[i].set_title('%s\n(avg = %.0f, diff = %.0f, p = %.3f)' % (name, avg, diff, pval))
    plt.tight_layout()
    plt.ylim([0, 1000])

### How many people want to give more during matches?

def plot_h3():
    g = sns.factorplot(MATCHER, AMOUNT, LIMIT, hue_order=('Yes', 'No'),
                       data=data_melted_challenge, kind='bar', x_order=ORG_NAMES)
    plt.title("Average donation to a challenge campaign")

def plot_h3_2():
    f, ax = plt.subplots(1, 3, sharey=True)
    for i, (org, name) in enumerate(ORGS_AND_NAMES):
        yes = data[org+'_donation_challenge']
        no = data[org+'_donation_nochallenge']
        zero = (yes == 0)
        yes = yes[~zero]
        no = no[~zero]
        YES = 'Below limit'
        NO = 'Above limit'
        df = pd.DataFrame({ YES: yes, NO: no })[[YES, NO]]
        diff = (no - yes).mean()
        t, pval = scipy.stats.ttest_1samp((no - yes), 0)
        sns.violinplot(df, inner='box', join_rm=True, ax=ax[i])
        avg = yes.mean()
        ax[i].set_title('%s\n(avg = %.0f, diff = %.0f, p = %.3f)' % (name, avg, diff, pval))
    plt.tight_layout()
    plt.ylim([0, 1000])

### Do people want to donate more to matches or challenges?

def plot_h4():
    # NOTE: the large difference between HEA here is because one
    # person said they would donate $5k to the match and $0 to the
    # challenge. TODO: remove outlier and recompute?
    sns.factorplot(MATCHER, AMOUNT, 'type', hue_order=('Match', 'Challenge'),
                   data=data_melted_mvsc, kind='bar', x_order=ORG_NAMES)
    plt.title("Average donation, match vs. challenge (when under limit)")

def plot_h4_2():
    f, ax = plt.subplots(1, 3, sharey=True)
    for i, (org, name) in enumerate(ORGS_AND_NAMES):
        yes = data[org+'_donation_match']
        no = data[org+'_donation_challenge']
        zero = (yes == 0)
        yes = yes[~zero]
        no = no[~zero]
        YES = 'Match'
        NO = 'Challenge'
        df = pd.DataFrame({ YES: yes, NO: no })[[YES, NO]]
        diff = (no - yes).mean()
        t, pval = scipy.stats.ttest_1samp((no - yes), 0)
        sns.violinplot(df, inner='box', join_rm=True, ax=ax[i])
        avg = yes.mean()
        ax[i].set_title('%s\n(avg = %.0f, diff = %.0f, p = %.3f)' % (name, avg, diff, pval))
    plt.tight_layout()
    plt.ylim([0, 1000])

def plot_h4_3():
    # Why are HEA estimates so different for match vs challenge?
    sns.violinplot(data[['HEA_donation_match', 'HEA_donation_challenge']],
                   inner='points', data=data_melted_mvsc)
    plt.title("HEA donations, match vs. challenge")

### To what extent do people donate less if they believe the counterfactual is more important?

def get_cf_status(num):
    if num == 0:
        return 'none'
    elif num < 10:
        return 'partial'
    else:
        return 'full'

def plot_h5():
    df = pd.DataFrame(columns=[MATCHER, 'decrease', 'counterfactual'], index=[])
    for org, name in ORGS_AND_NAMES:
        cf_match = data['%s_cf_match' % org]
        cf_nomatch = data['%s_cf_nomatch' % org]
        diff = cf_match - cf_nomatch
        counterfactual = diff.apply(get_cf_status)

        donation_match = data['%s_donation_match' % org]
        donation_nomatch = data['%s_donation_nomatch' % org]
        decrease = donation_match - donation_nomatch

        df = pd.concat([df, pd.DataFrame({
            MATCHER: name, 'decrease': decrease, 'counterfactual': counterfactual
        })])

    # TODO(ben): fix bad layout
    sns.factorplot(MATCHER, 'decrease', 'counterfactual', data=df,
                   x_order=ORG_NAMES, hue_order=('full', 'partial', 'none'),
                   legend=False)
    plt.legend(loc='upper left')
    plt.title("Donation reduction by belief about counterfactual")

from matplotlib.pylab import rcParams
rcParams['figure.figsize'] = 7.5, 4

sns.set_style('whitegrid', {'legend.frameon':True})
plot_h1()
plt.savefig('figures/counterfactual.svg')
plot_h2()
plt.savefig('figures/match.svg')
plot_h2_2()
plt.savefig('figures/match_detail.svg')
plot_h3()
plt.savefig('figures/challenge.svg')
plot_h3_2()
plt.savefig('figures/challenge_detail.svg')
plot_h4()
plt.savefig('figures/mvsc.svg')
plot_h4_2()
plt.savefig('figures/mvsc_detail.svg')
plot_h5()
plt.savefig('figures/decrease_by_cf.svg')
