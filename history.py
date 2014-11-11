# Get detailed information out of the Stacks project history
import subprocess
import re
import Levenshtein

# For the moment we only look at these environments in the latex source files
with_proofs = ['lemma', 'proposition', 'theorem']
without_proofs = ['definition', 'example', 'exercise', 'situation', 'remark', 'remarks']


# each of these will collect the following data
# name texfile, type, latex_label, tag,
# line_nr of begin{env}, line_nr of end{env}, text of env,
# line_nr of begin{proof}, line_nr of end{proof}, text of proof
class env_with_proof:
	def __init__(self, name, type, label, tag, b, e, text, bp, ep, proof):
		self.name = name
		self.type = type
		self.label = label
		self.tag = tag
		self.b = b
		self.e = e
		self.text = text
		self.bp = bp
		self.ep = ep
		self.proof = proof


def print_with(With):
	print With.name
	print With.type
	print With.label
	print With.tag
	print With.b
	print With.e
	print With.text.rstrip()
	print With.bp
	print With.ep
	print With.proof.rstrip()


# each of these will collect the following data
# name texfile, type, latex_label, tag,
# line_nr of begin{env}, line_nr of end{env}, text of env
class env_without_proof:
	def __init__(self, name, type, label, tag, b, e, text):
		self.name = name
		self.type = type
		self.label = label
		self.tag = tag
		self.b = b
		self.e = e
		self.text = text


def print_without(Without):
	print Without.name
	print Without.type
	print Without.label
	print Without.tag
	print Without.b
	print Without.e
	print Without.text.rstrip()


def print_env(env):
	if env.type in with_proofs:
		print_with(env)
		return
	if env.type in without_proofs:
		print_without(env)
		return
	print "Unknown type!"
	exit(1)


# Finds all environments in stacks-project/name.tex
# and returns it as a pair [envs_with_proofs, envs_without_proofs] of lists
# of classes as above
def get_envs(name):

	# We will store all envs in the following list
	envs = []

	# Initialize an empty environment with proof
	With = env_with_proof('', '', '', '', 0, 0, '', 0, 0, '')
	# Initialize an empty environment without proof
	Without = env_without_proof('', '', '', '', 0, 0, '')

	try:
		texfile = open('stacks-project/' + name + '.tex', 'r')
	except:
		return envs

	line_nr = 0
	in_with = 0
	need_proof = 0
	in_proof = 0
	in_without = 0
	for line in texfile:
		line_nr = line_nr + 1

		if in_proof:
			With.proof += line
			if line.find('end{proof}') >= 0:
				With.ep = line_nr
				in_proof = 0
				envs.append(With)
				With = env_with_proof('', '', '', '', 0, 0, '', 0, 0, '')

		if in_with:
			With.text += line
			if line.find('end{' + With.type + '}') >= 0:
				With.e = line_nr
				need_proof = 1
				in_with = 0

		if in_without:
			Without.text += line
			if line.find('end{' + Without.type + '}') >= 0:
				Without.e = line_nr
				in_without = 0
				envs.append(Without)
				Without = env_without_proof('', '', '', '', 0, 0, '')

		if line.find('begin{') >= 0:

			# Ignore a proof if we do not need one
			if need_proof and line.find('begin{proof}') >= 0:
				With.proof = line
				With.bp = line_nr
				in_proof = 1
				need_proof = 0

			for type in with_proofs:
				if line.find('begin{' + type + '}') >= 0:
					# wipe out unfinished environment
					if in_with:
						With = env_with_proof('', '', '', '', 0, 0, '', 0, 0, '')
						in_with = 0
					# no proof present, but finished
					elif need_proof:
						envs.append(With)
						With = env_with_proof('', '', '', '', 0, 0, '', 0, 0, '')
						need_proof = 0
					# unfinished proof for finished environment
					elif in_proof:
						With.bp = 0
						With.ep = 0
						With.proof = ''
						envs.append(With)
						With = env_with_proof('', '', '', '', 0, 0, '', 0, 0, '')
						in_proof = 0
					# wipe out unfinished environment
					if in_without:
						Without = env_without_proof('', '', '', '', 0, 0, '')
						in_without = 0
					With.name = name
					With.type = type
					if not With.label == '':
						print "Label with already present"
						exit(1) # check logic
					With.b = line_nr
					With.text = line
					in_with = 1

			for type in without_proofs:
				if line.find('begin{' + type + '}') >= 0:
					# wipe out unfinished environment
					if in_with:
						With = env_with_proof('', '', '', '', 0, 0, '', 0, 0, '')
						in_with = 0
					# no proof yet but a definition or such in between lemma and proof allowed
					elif need_proof:
						pass
					# unfinished proof for finished environment
					elif in_proof:
						With.bp = 0
						With.ep = 0
						With.proof = ''
						envs.append(With)
						With = env_with_proof('', '', '', '', 0, 0, '', 0, 0, '')
						in_proof = 0
					# wipe out unfinished environment
					if in_without:
						Without = env_without_proof('', '', '', '', 0, 0, '')
						in_without = 0
					Without.name = name
					Without.type = type
					if not Without.label == '':
						print "Label without already present"
						exit(1) # check logic
					Without.text = line
					Without.b = line_nr
					in_without = 1

		# Only first label gets picked
		if (in_with and With.label == '') or (in_without and Without.label == ''):
			n = line.find('\\label{')
			if n >= 0:
				n = n + 6
				m = line.find('}', n)
				label = line[n + 1 : m]
				if in_with:
					With.label = label
				else:
					Without.label = label

	# Clean up
	# wipe out unfinished environment
	if in_with:
		With = env_with_proof('', '', '', '', 0, 0, '', 0, 0, '')
		in_with = 0
	# no proof
	elif need_proof:
		envs.append(With)
		With = env_with_proof('', '', '', '', 0, 0, '', 0, 0, '')
		need_proof = 0
	# unfinished proof for finished environment
	elif in_proof:
		With.bp = 0
		With.ep = 0
		With.proof = ''
		envs.append(With)
		With = env_with_proof('', '', '', '', 0, 0, '', 0, 0, '')
		in_proof = 0
	# wipe out unfinished environment
	if in_without:
		Without = env_without_proof('', '', '', '', 0, 0, '')
		in_without = 0
	# close texfile
	texfile.close()
	return envs


# Finds all tags if there are any
def find_tags():
	tags = []
	try:
		tagsfile = open("stacks-project/tags/tags", 'r')
		for line in tagsfile:
			if not line.find('#') == 0:
				tags.append(line.rstrip().split(","))
	except:
		pass
	return tags


# Finds all commits in stacks-project
def find_commits():
	commits = subprocess.check_output(["git", "-C", "stacks-project", "log", "--pretty=format:%H", "master"])
	# Reverse the list so that 0 is the first one
	return commits.splitlines()[::-1]

# gets next commit
def next_commit(commit):
	commits = find_commits()
	i = 0
	while i < len(commits) - 1:
		if commit == commits[i]:
			return commits[i + 1]
		i = i + 1
	print "There is no next commit!"
	return ''

# Get tex file names out of list of files
def get_names(temp):
	names = []
	# Get rid of files in subdirectories
	# Get rid of non-tex files
	# Get rid of the .tex ending
	for i in range(0, len(temp)):
		file_name = temp[i]
		if file_name.find('/') >= 0:
			continue
		if '.tex' not in file_name:
			continue
		names.append(file_name[:-4])
	return names


# Checks out the given commit in stacks-project
def checkout_commit(commit):
	devnull = open('/dev/null', 'w')
	subprocess.call(["git", "-C", "stacks-project", "checkout", commit], stdout = devnull, stderr = devnull)
	devnull.close()


# List files in given commit
def get_names_commit(commit):
	temp = subprocess.check_output(["git", "-C", "stacks-project", "ls-tree", "--name-only", commit])
	return get_names(temp.splitlines())


# Get diff between two commits in a given file
# commit_before should be prior in history to commit_after
def get_diff_in(commit_before, commit_after, name):
	diff = subprocess.check_output(["git", "-C", "stacks-project", "diff", "--patience", "-U0", commit_before + '..' + commit_after, '--', name + '.tex'])
	return diff.splitlines()


# Regular expressions to parse diffs
two_commas = re.compile('\@\@\ \-([0-9]*)\,([0-9]*)\ \+([0-9]*)\,([0-9]*)\ \@\@')
first_comma = re.compile('\@\@\ \-([0-9]*)\,([0-9]*)\ \+([0-9]*)\ \@\@')
second_comma = re.compile('\@\@\ \-([0-9]*)\ \+([0-9]*)\,([0-9]*)\ \@\@')
no_comma = re.compile('\@\@\ \-([0-9]*)\ \+([0-9]*)\ \@\@')


# Gets a list of line_nr changes between two commits
# in a given file
# commit_before should be prior in history to commit_after
def get_changes_in(commit_before, commit_after, name):

	diff = get_diff_in(commit_before, commit_after, name)

	lines_removed = []
	lines_added = []

	for line in diff:
		if line.find('@@') == 0:
			# The line looks like
			# @@ -(old line nr),d +(new line nr),a @@
			# meaning 5 lines where removed from old file starting at
			# old line nr and a lines were added started at new line nr
			# Variant: ',d' is missing if d = 1
			# Variant: ',a' is missing if a = 1
			# total of 4 cases matching the regular expressions compiled above

			result = two_commas.findall(line)

			if len(result) == 1 and len(result[0]) == 4:
				lines_removed.append([int(result[0][0]), int(result[0][1])])
				lines_added.append([int(result[0][2]), int(result[0][3])])
				continue

			result = first_comma.findall(line)

			if len(result) == 1 and len(result[0]) == 3:
				lines_removed.append([int(result[0][0]), int(result[0][1])])
				lines_added.append([int(result[0][2]), 1])
				continue

			result = second_comma.findall(line)

			if len(result) == 1 and len(result[0]) == 3:
				lines_removed.append([int(result[0][0]), 1])
				lines_added.append([int(result[0][1]), int(result[0][2])])
				continue

			result = no_comma.findall(line)

			if len(result) == 1 and len(result[0]) == 2:
				lines_removed.append([int(result[0][0]), 1])
				lines_added.append([int(result[0][1]), 1])
				continue

			print "Unexpected format of following diff line: "
			print line
			exit(1)

	return [lines_removed, lines_added]


# Gets a list of files changed between two commits
# commit_before should be prior in history to commit_after
def get_names_changed(commit_before, commit_after):
	temp = subprocess.check_output(["git", "-C", "stacks-project", "diff", "--name-only", commit_before + '..' + commit_after])
	return get_names(temp.splitlines())


# Gets a list of line_nr changes between two commits
# commit_before should be prior in history to commit_after
def get_all_changes(commit_before, commit_after):

	all_changes = {}

	files_changed = get_names_changed(commit_before, commit_after)

	for name in files_changed:
		all_changes[name] = get_changes_in(commit_before, commit_after, name)

	return all_changes


# Regular expression matching removed and added tags
deleted_tag = re.compile('^\-([0-9A-Z]{4})\,(.*)')
added_tag = re.compile('^\+([0-9A-Z]{4})\,(.*)')


# Gets a list of tag changes between two commits
# commit_before should be prior in history to commit_after
def get_tag_changes(commit_before, commit_after):

	tags_removed = []
	tags_added = []

	diff = subprocess.check_output(["git", "-C", "stacks-project", "diff", "--patience", "-U0", commit_before + '..' + commit_after, '--', 'tags/tags'])
	diff = diff.splitlines()

	for line in diff:
		deleted = deleted_tag.findall(line)
		if len(deleted) > 0:
			tags_removed.append([deleted[0][0], deleted[0][1]])
		added = added_tag.findall(line)
		if len(added) > 0:
			tags_added.append([added[0][0], added[0][1]])

	return [tags_removed, tags_added]


# Find tags whose labels got changed
def tags_changed_labels(tag_changes):
	tags_changed = []
	tags_removed = tag_changes[0]
	tags_added = tag_changes[1]
	n = len(tags_removed)
	m = len(tags_added)
	i = 0
	j = 0
	while (i < n) and (j < m):
		if tags_removed[i][0] == tags_added[j][0]:
			tags_changed.append([tags_removed[i][0], tags_removed[i][1], tags_added[i][1]])
			i = i + 1
			continue
		if tags_removed[i][0] < tags_added[j][0]:
			i = i + 1
			continue
		j = j + 1
	return tags_changed

# Print changes functions
def print_diff(diff):
	for line in diff:
		print line

def print_changes(changes):
	lines_removed = changes[0]
	lines_added = changes[1]
	print "Removed:"
	for line, count in lines_removed:
		print line, count
	print "Added:"
	for line, count in lines_added:
		print line, count

def print_all_changes(all_changes):
	for name in all_changes:
		print "In file " + name + ".tex:"
		print_changes(all_changes[name])

def print_tag_changes(tag_changes):
	print 'Removed:'
	for tag, label in tag_changes[0]:
		print tag + ',' + label
	print 'Added:'
	for tag, label in tag_changes[1]:
		print tag + ',' + label
	print 'Changed:'
	tag_mod = tags_changed_labels(tag_changes)
	for tag, oldlabel, newlabel in tag_mod:
		print tag + ' : ' + oldlabel + ' ---> ' + newlabel


# Add tags to a list of environments
# Overwrites already existing tags
def add_tags(envs, tags):
	for env in envs:
		long_label = env.name + '-' + env.label
		for tag, label in tags:
			if label == long_label:
				env.tag = tag
				continue


# Get all envs from a commit
# Should only be used for the initial commit
def get_all_envs(commit):

	all_envs = {}

	# get names
	names = get_names_commit(commit)

	# Checkout the commit
	checkout_commit(commit)

	# loop through tex files and add envs
	for name in names:
		all_envs[name] = get_envs(name)

	return all_envs


# Storing history of an env
# commit and env are current (!)
# commits is a list of the commits that changed our env
# here 'change' means anything except for moving the text
# envs is the list of states of the env during those commits
class env_history:
	def __init__(self, commit, env, commits, envs):
		self.commit = commit
		self.env = env
		self.commits = commits
		self.envs = envs

# Initialize an env_history
def initial_env_history(commit, env):
	return env_history(commit, env, [commit], [env])

# Update an env_history with a given commit and env
# This replaces the current state as well!
def update_env_history(env_h, commit, env):
	# Move commit and env to the end of the lists
	env_h.commits.append(commit)
	env_h.envs.append(env)
	env_h.commit = commit
	env_h.env = env

# overall history
# commit is current commit
# env_histories is a list of env_history objects
# commits is list of previous commits with
# commits[0] the initial one
class history:
	def __init__(self, commit, env_histories, commits):
		self.commit = commit
		self.env_histories = env_histories
		self.commits = commits

def print_history_stats(History):
	print "We are at commit: " + History.commit
	print "We have done " + str(len(History.commits)) + " previous commits:"
	print "We have " + str(len(History.env_histories)) + " histories"
	names = {}
	types = {}
	d = 0
	for env_h in History.env_histories:
		name = env_h.env.name
		if name in names:
			names[name] += 1
		else:
			names[name] = 1
		type = env_h.env.type
		if type in types:
			types[type] += 1
		else:
			types[type] = 1
		if len(env_h.commits) > d:
			d = len(env_h.commits)
	print
	print "Maximum depth is: " + str(d)
	print
	for name in names:
		print "We have " + str(names[name]) + " in " + name
	print
	for type in types:
		print "We have " + str(types[type]) + " of type " + type


# Initialize history
def initial_history():
	initial_commit = '3d32323ff9f1166afb3ee0ecaa10093dc764a50d'
	all_envs = get_all_envs(initial_commit)
	env_histories = []
	# there are no tags present so we do not need to add them
	for name in all_envs:
		for env in all_envs[name]:
			env_h = initial_env_history(initial_commit, env)
			env_histories.append(env_h)
	return history(initial_commit, env_histories, [])

# Logic for pairs: return
#	-1 if start + nr - 1 < b
#	0  if intervals meet
#	1  if e < start
def logic_of_pairs(start, nr, b, e):
	# If nr = 0, then change starts at start + 1
	if nr == 0:
		if start < b:
			return -1
		if e <= start:
			return 1
		return 0
	# now nr > 0 so change starts at start and ends at start + nr - 1
	if e < start:
		return 1
	if start + nr - 1 < b:
		return -1
	return 0

# Compute shift
def compute_shift(lines_removed, lines_added, i):
	if lines_removed[i][1] > 0 and lines_added[i][1] > 0:
		return lines_added[i][0] + lines_added[i][1] - lines_removed[i][0] - lines_removed[i][1]
	if lines_removed[i][1] == 0:
		return lines_added[i][0] + lines_added[i][1] - lines_removed[i][0] - 1
	if lines_added[i][1] == 0:
		return lines_added[i][0] + 1 - lines_removed[i][0] - lines_removed[i][1]
	print "Should not happen!"
	exit(1)

# See if env from commit_before is changed
# If not changed, but moved inside file, then update line numbers
def env_before_is_changed(env, all_changes):
	if not env.name in all_changes:
		return False
	lines_removed = all_changes[env.name][0]
	lines_added = all_changes[env.name][1]
	i = 0
	while i < len(lines_removed):
		start =  lines_removed[i][0]
		nr = lines_removed[i][1]
		position = logic_of_pairs(start, nr, env.b, env.e)
		if position == 0:
			return True
		if position == 1:
			break
		i = i + 1

	# adjust line numbers; i is index of chunk just beyond env
	if i > 0:
		shift = compute_shift(lines_removed, lines_added, i - 1)
		env.b = env.b + shift
		env.e = env.e + shift

	if env.type in without_proofs:
		return False
	if env.proof == '':
		return False

	# The proof could still be after the chunk we are at
	while i < len(lines_removed):
		start =  lines_removed[i][0]
		nr = lines_removed[i][1]
		position = logic_of_pairs(start, nr, env.bp, env.ep)
		if position == 0:
			return True
		if position == 1:
			break
		i = i + 1

	# adjust line numbers; i is the index of chunk just beyond proof of env
	if i > 0:
		shift = compute_shift(lines_removed, lines_added, i - 1)
		env.bp = env.bp + shift
		env.ep = env.ep + shift

	return False

# See if env from commit_after is new or changed
def env_after_is_changed(env, all_changes):
	if not env.name in all_changes:
		return False
	lines_added = all_changes[env.name][1]
	for start, nr in lines_added:
		if logic_of_pairs(start, nr, env.b, env.e) == 0:
			return True
	if env.type in without_proofs:
		return False
	if env.proof == '':
		return False
	for start, nr in lines_added:
		if logic_of_pairs(start, nr, env.bp, env.ep) == 0:
			return True
	return False


# Simplest kind of match: name, label, type all match
def simple_match(env_b, env_a):
	if (env_b.name == env_a.name and env_b.type == env_a.type and env_b.label == env_a.label and not env_a.label == ''):
		print "MATCH name, type, label!"
		return True
	return False

# Match text statement exactly when no labels present
# We also need to match the file as there is an example where the exact same statement occurs in different files.
def text_match(env_b, env_a):
	if env_b.label == '' and env_a.name == env_b.name and env_a.text == env_b.text:
		print "Match name, text, no label!"
		return True
	return False
	

# Next easiest to detect: label got changed and we recorded this in the tags file
def tag_mod_match(env_b, env_a, tag_mod):
	for tag, label_b, label_a in tag_mod:
		if (env_b.name + '-' + env_b.label == label_b and env_a.name + '-' + env_a.label == label_a):
			print "MATCH by label change in tags/tags!"
			if not env_a.tag == tag:
				print "No or incorrect tag where there should be one!"
				exit(1)
			return True
	return False

# Closeness score
def closeness_score(env_b, env_a):
	score = 0
	if env_b.name == env_a.name:
		score = score + 0.05
	if env_b.type == env_a.type:
		score = score + 0.05
	if env_b.label == env_a.label and not env_b.label == '':
		score = score + 0.1
	return(score + Levenshtein.ratio(env_b.text, env_a.text))


# Main function, going from history for some commit to the next
#
# Problem we ignore for now: history is not linear
#
def update_history(History):
	commit_before = History.commit
	commit_after = next_commit(commit_before)
	all_changes = get_all_changes(commit_before, commit_after)

	# List of env_histories which are being changed
	envs_h_b = []
	labels_present = []
	for env_h in History.env_histories:
		env = env_h.env
		if not env.label == '':
			if env.name + '-' + env.label in labels_present:
				print "Error: Double label!"
				print_env(env)
				exit(1)
			else:
				labels_present.append(env.name + '-' + env.label)
                # The following line also updates line numbers
		if env_before_is_changed(env, all_changes):
			envs_h_b.append(env_h)
		else:
			# We are current for commit_after
			# except for maybe a tag change
			env_h.commit = commit_after

	# List of new or changed envs
	envs_a = []
	checkout_commit(commit_after)
	for name in all_changes:
		envs = get_envs(name)
		for env in envs:
			if env_after_is_changed(env, all_changes):
				envs_a.append(env)
				# Unfortunately, it may happen that the edit consisted of adding
				# a nonexistent proof to an env already in History. This would
				# not have been detected above, so we need to look for these and
				# add them to envs_h_b if necessary
				for env_h in History.env_histories:
					if env_h.env.name == env.name and env_h.env.text == env.text:
						if not env_h in envs_h_b:
							envs_h_b.append(env_h)
			else:
				# check existence and line numbers
				found = 0
				for env_h in History.env_histories:
					if env_h.env.name == env.name and env_h.env.text == env.text:
						found = 1
						if not (env_h.env.b == env.b and env_h.env.e == env.e):
							print
							print "Warning: Wrong line numbers or double environment."
							print_env(env_h.env)
							print_env(env)
							print_all_changes(all_changes)
				if not found:
					print
					print "Error: environment not found in History."
					exit(1)


	# Get tag changes
	tag_changes = get_tag_changes(commit_before, commit_after)
	tag_del = tag_changes[0]
	tag_new = tag_changes[1]
	tag_mod = tags_changed_labels(tag_changes)

	# Endow new or changed envs with new tags
	# Just to put more information into envs_a before updating histories
	add_tags(envs_a, tag_new)

	# Give feedback
	print
	print "Changed before " + str(len(envs_h_b)) + " and after " + str(len(envs_a))
	print "Listing before labels:"
	for env_h in envs_h_b:
		print env_h.env.label
	print "Listing after labels:"
	for env_a in envs_a:
		print env_a.label

	# Try to match environments between changes
	# First time through
	i = 0
	while i < len(envs_h_b):
		env_b = envs_h_b[i].env
		j = 0
		while j < len(envs_a):
			env_a = envs_a[j]
			if simple_match(env_b, env_a):
				break
			if text_match(env_b, env_a):
				break
			if tag_mod_match(env_b, env_a, tag_mod):
				break
			j = j + 1

		# This means we have a match with given i and j
		if j < len(envs_a):
			update_env_history(envs_h_b[i], commit_after, envs_a[j])
			del envs_h_b[i]
			del envs_a[j]
			# do not change i here
		else:
			i = i + 1


	# Second time through
	i = 0
	while i < len(envs_h_b):
		env_b = envs_h_b[i].env
		j = 0
		best_j = -1
		score = 0
		while j < len(envs_a):
			env_a = envs_a[j]
			new_score = closeness_score(env_b, env_a)
			if new_score > score:
				best_j = j
				score = new_score
			j = j + 1
		if score > 0.95:
			print "MATCH by score!"
			update_env_history(envs_h_b[i], commit_after, envs_a[best_j])
			del envs_h_b[i]
			del envs_a[best_j]
			# do not change i here
		else:
			print "No match found; best score: " + str(score)
			print_without(env_b)
			if best_j >= 0:
				print "Best match:"
				print_without(envs_a[best_j])
			else:
				print "No new envs left over!"
			print "Removing..."
			History.env_histories.remove(envs_h_b[i])
			i = i + 1

	# More feedback
	print "Left over from before " + str(len(envs_h_b)) + " and from after " + str(len(envs_a))
	for env_h in envs_h_b:
		print_without(env_h.env)

	# add tags to envs
	for tag, label in tag_new:
		nr_matches = 0
		for env_h in History.env_histories:
			env = env_h.env
			if env.name + '-' + env.label == label:
				nr_matches = nr_matches + 1
				if nr_matches > 1:
					print "Error: multiple matches for tag: " + tag
					print "with label: " + label
					exit(1)
				if not env.tag == '':
					good = 0
					for tag_m, label_b, label_a in tag_mod:
						if tag == tag_m:
							good = 1
					if not good:
						print "Error: modified tag not detected!"
						exit(1)
				env.tag = tag

	# TODO: Check for histories with deleted tags

	# Add left over newly created envs to History
	for env_a in envs_a:
		env_h = initial_env_history(commit_after, env_a)
		if env_a.label == 'lemma-flat':
			print "ADDING IT HERE"
			print_env(env_a)
		History.env_histories.append(env_h)
	# Change current commit
	History.commits.append(commit_before)
	History.commit = commit_after


# Testing, testing

History = initial_history()
print
print_history_stats(History)

for i in range(1000):
	update_history(History)
	print
	print "Finished with commit: " + History.commit
	print
	for env_h in History.env_histories:
		if env_h.env.label == 'lemma-flat':
			print 'AAAAAAAAA'
			print env_h.env.b
			print env_h.env.e
	# print_history_stats(History)

###
#commits = find_commits()
#i = 0
#while True:
#	tag_changes = get_tag_changes(commits[i], commits[i + 1])
#	if (len(tag_changes[0]) > 0) and (len(tag_changes[1]) > 0):
#		tag_mod = tags_changed_labels(tag_changes)
#		if len(tag_mod) > 0:
#			print i + 1
#			print_tag_changes(tag_changes)
#			if (len(tag_mod) < len(tag_changes[0])) and (len(tag_mod) < len(tag_changes[1])):
#				exit(0)
#	i = i + 1


def test_change_tag():
	# In the commit
	# 42c1b1fb6bedb113f0d89a8af7124122f91009b6 (with parent aca72ce327581a43ec2f56952a551edc751b4058 )
	# we change a latex label
	tag_changes = get_tag_changes('aca72ce327581a43ec2f56952a551edc751b4058', '42c1b1fb6bedb113f0d89a8af7124122f91009b6')
	print_tag_changes(tag_changes)
	# Between
	# 8de7ea347d2e3ec3689aa84041e9d5ced52963cb
	# and
	# 2799b450a9a7a5a02932033b43f43d406e1a6b33
	# have interesting tag changes
	#
	tag_changes = get_tag_changes('2799b450a9a7a5a02932033b43f43d406e1a6b33', '8de7ea347d2e3ec3689aa84041e9d5ced52963cb')
	print_tag_changes(tag_changes)
	# Another example
	#
	commits = find_commits()
	tag_changes = get_tag_changes(commits[928], commits[929])
	print_tag_changes(tag_changes)


def test_adding_tags_to_envs():
	# list all commits
	commits = find_commits()
	# Stacks epoch occurs at
	# fad2e125112d54e1b53a7e130ef141010f9d151d
	# which is commits[533]
	n = 1533
	name = 'algebra'
	checkout_commit(commits[n])
	envs = get_envs('algebra')
	tags = find_tags()
	for env in envs:
		if not env.tag == '':
			print_env(env)
			print "Should not happen!"
			exit(1)
	add_tags(envs, tags)
	for env in envs:
		if env.tag == '':
			print_env(env)


def test_finding_changes(commit_before, commit_after):

	names = get_names_changed(commit_before, commit_after)
	print names

	for name in names:
		diff = get_diff_in(commit_before, commit_after, name)
		print_diff(diff)

		changes = get_changes_in(commit_before, commit_after, name)
		print_changes(changes)

	all_changes = get_all_changes(commit_before, commit_after)
	print_all_changes(all_changes)

#commits = find_commits()
#test_finding_changes(commits[11], commits[12])
