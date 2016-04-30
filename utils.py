import re

# Simplify the intervals array returning a new array simplified.
def remove_overlap( intervals ): #sol by http://www.geeksforgeeks.org/merging-intervals/
	sorted_by_lower_bound = sorted(intervals, key=lambda tup: tup[0])
	merged = []

	for higher in sorted_by_lower_bound:
		if not merged:
			merged.append(higher)
		else:
			lower = merged[-1]
			# test for intersection between lower and higher:
			# we know via sorting that lower[0] <= higher[0]
			if higher[0] <= lower[1]:
				upper_bound = max(lower[1], higher[1])
				merged[-1] = (lower[0], upper_bound)  # replace by merged interval
			else:
				merged.append(higher)
	return merged

# Parse a string representation of an interval array toa  real interval array.
def getIntervalArray( intervals ):
	regex = re.compile("\(\d+,\d+\)")
	result = []
	for match in regex.finditer(intervals):
		interval = eval(match.group(0))
		if( interval[0] < interval[1] and interval[0] >= 0 and interval[1] >= 1):
			result.append(interval)
	return result

def isInt(s):
		try: 
			int(s)
			return True
		except ValueError:
			return False