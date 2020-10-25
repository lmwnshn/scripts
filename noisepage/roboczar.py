import time

import github
import jenkinsapi


# Jenkins URL.
jurl = r''
# Jenkins username.
juser = ''
# Jenkins API token from the Configure page.
jpass = ''
# Github personal access token with repo rights.
gtok = ''

prs = [
    #  {
    #    'num'     : -1,  # PR number.
    #    'title'   : '',  # Merge commit title.
    #    'message' : '',  # Merge commit message. Remember coauthors!
    #  },
]


def be_patient(num_seconds):
    print('Python: sleep {} seconds.'.format(num_seconds))
    time.sleep(num_seconds)


def retry_until_good(J, job_name):
    passing = False
    while not passing:
        job = J.get_job(job_name)
        build = job.get_last_build()
        print('Jenkins: {} build {}'.format(job_name, build.buildno))

        if build.is_running():
            print('Jenkins: {} still running, waiting...'.format(job_name))
            be_patient(300)
            continue

        if build.is_good():
            print('Jenkins: {} build {} is good.'.format(job_name, build.buildno))
            passing = True
        else:
            print('Jenkins: {} build {} failed.'.format(job_name, build.buildno))
            print('Jenkins: trigger build {}.'.format(job_name))
            J.build_job(job_name)
            be_patient(10)


def merge_pr(J, G, pr):
    repo = G.get_repo('cmu-db/noisepage')
    pull = repo.get_pull(pr['num'])
    pr_name = 'PR-{}'.format(pr['num'])

    print('Python: next PR up, {}.'.format(pr_name))

    # Update the branch on GitHub if necessary.
    if pull.mergeable_state == 'blocked':
        print('GitHub: MS blocked, may have failed CI, {}.'.format(pr_name))
    elif pull.mergeable_state == 'behind':
        print('GitHub: MS behind, updating {}.'.format(pr_name))
        update_success = pull.update_branch()
        if not update_success:
            raise Exception('Could not update {}. Stop!'.format(pr_name))
        print('GitHub: updated {}.'.format(pr_name))
        print('Jenkins: trigger build {}.'.format(pr_name))
        J.build_job(pr_name)
        be_patient(10)
    elif pull.mergeable_state == 'clean':
        print('GitHub: MS clean, continuing {}.'.format(pr_name))
    else:
        raise Exception('Could not get good merge status for {}. Stop!'.format(pr_name))

    # Check if the job is passing on Jenkins.
    retry_until_good(J, pr_name)

    # Merge the PR on GitHub.
    print('Github: merging {}.'.format(pr_name))
    merge_status = pull.merge(pr['message'], pr['title'], 'squash')
    if not merge_status.merged:
        raise Exception('Could not merge {}. Stop!'.format(pr_name))
    print('Github: merged {}.'.format(pr_name))


def merge_prs():
    print('The PRs to MERGE are:')
    for i, pr in enumerate(prs, 1):
        print('--------------------------------------------------------------')
        print(i, pr['num'])
        print(pr['title'])
        print(pr['message'])
        print('--------------------------------------------------------------')
        print()
    should_continue = input('Continue? [y/n] : ')
    if should_continue.lower() == 'y':
        print('Continuing.')
        J = jenkinsapi.jenkins.Jenkins(jurl, username=juser, password=jpass)
        print('Jenkins: connected as {}.'.format(juser))
        G = github.Github(gtok)
        print('GitHub: connected.')
        for pr in prs:
            merge_pr(J, G, pr)


def retry_prs():
    jobs = []
    print('Enter Jenkins jobs to retry (one per line, END to stop).\n')

    done = False
    while not done:
        job_name = input('Job: ').strip()
        if job_name.lower() == 'end':
            done = True
        else:
            jobs.append(job_name)

    print('The jobs to RETRY are:')
    for i, job in enumerate(jobs, 1):
        print('--------------------------------------------------------------')
        print(i, job)
        print('--------------------------------------------------------------')
        print()
    should_continue = input('Continue? [y/n] : ')
    if should_continue.lower() == 'y':
        print('Continuing.')
        J = jenkinsapi.jenkins.Jenkins(jurl, username=juser, password=jpass)
        print('Jenkins: connected as {}.'.format(juser))
        for job in jobs:
            retry_until_good(J, job)


def main():
    option = input('M for merge, R for retry. [M/R] : ')
    if option.lower() == 'm':
        merge_prs()
    elif option.lower() == 'r':
        retry_prs()
    else:
        print('Unknown option: {}'.format(option))


if __name__ == '__main__':
    main()

