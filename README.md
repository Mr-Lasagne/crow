# CROW: Clerical Resolution Online Widget

## About

The Clerical Resolution Online Widget (CROW) is an open-source application
designed to facilitate the clerical review of linked data.

CROW reads linked data files, presents it in an easy-to-read-and-compare format,
and has tools that can help the clerical reviewer with match/non-match
decisions.

## Aims

CROW aims to:

- Meet the clerical matching needs of both large and small scale projects.
- Get clerical matching results faster compared to other free to us software.
- Minimise error during clerical review by presenting record pair data one at a
  time and in a easy-to-read-and-compare format.
- Be easy to use for the clerical matcher when reviewing record pairs and the
  clerical coordinator setting up the project.
- Be open and transparent, so the community can use the software without
  restrictions.

## Installation and Use

There are currently two available versions of CROW: CROW1 and CROW2. CROW1 is a
Python desktop application and can be run in or outside of the Data Access
Platform (DAP). CROW2 is a web application that can be run in the Cloudera Data
Platform (CDP) inside or outside of DAP.

In addition to this GitHub repository, CROW exists in the Data Linkage Group as
a project in GitLab (within DAP).

## What is New?

The new version of CROW (CROW2) has been developed in Flask. The 'old' version
of CROW (CROW1) was initially written as a Python script using the package
Tkinter. For existing users, CROW1 is still available in the version1_tkinter
folder. CROW2 is available in the version2_flask folder.

We have moved to Flask from Tkinter because of its design and functionality
limitations - it only runs on desktop using Python and only imports CSV files.
Whereas Flask can use HTML functionality which has made it more accessible.

The app now has a 'select all' feature, a scroll bar, it can run in CDP and
interfaces directly with Hadoop Distributed File System (HDFS)/Hue/S3 buckets
and imports parquet files. This does however mean that, unlike CROW1, the app
works through CDP/Hive/HDFS only and cannot be run in any Python environment.
There is potential for this in future releases.

Previously, in CROW1, users were able to launch two different versions of the
app - pairwise and cluster - depending on whether they were working with pairs
or clusters of records. CROW2 has been consolidated into a single app.

## Documentation

The most up-to-date documentation can be found in the docs folders for each
version. There you will find instructions for setting CROW up for your project,
video demonstrations, and instructions you can give to your clerical matchers on
how to run CROW once it is set up.

## Accessibility

The CROW team have attempted to follow and implement accessibility requirements
to the best of their ability, but due to time and resource constraints it is not
likely all requirements will be met in the first release. However, the CROW team
aims for continuous development of the tool to meet accessibility requirements
with future releases.

The accessibility requirements are adapted from the 'Web Content Accessibility
Guidelines (WCAG) 2.0', which covers a wide range of recommendations for making
Web content more accessible. For more information on this, please visit:
<https://accessibility.18f.gov/checklist/>

Following these guidelines aims to make content accessible to a wider range of
people with disabilities, including blindness and low vision, deafness and
hearing loss, learning disabilities, cognitive limitations, limited movement,
speech disabilities, photosensitivity and combinations of these.

### Implemented in CROW2

The following features have been implemented in the current version of CROW2:

- Font formatting and style can be changed by the user depending on their
  preference Text size can be changed by zooming in and out.
- Arial font size 12 is the default font and size - for accessibility reasons.
- Brightness of items hovered over and then highlighted are 'muted' for users
  who find bright colours uncomfortable.
- The user interface can be zoomed into with no issues, magnifying what is on
  screen without making its contents illegible.
- 'Read aloud' works on CROW if opened in Microsoft Edge - but not in Google
  Chrome.

### Not Yet Implemented in CROW 2

The following features have not been implemented in the latest release of CROW,
but will be considered for future releases:

- Keyboard-tab accessibility.
- Background colours can be changed by user depending on their preference.
- Text colour and size.
- Records that are no longer available after matching are 'greyed out' so it is
  clear to users

If you have further accessibility requirements/needs please raise an issue in
the repository or contact the team directly.

## Acknowledgments

We are grateful to colleagues within the Data Linkage Hub and wider Office for
National Statistics for providing support, expert advice, and peer review of
this work.
