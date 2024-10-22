
# practical use interpretation --------------------------------------------



#consider the following morning rush hour flow matrix, with 2 "msoas"
flow_matrix = matrix(c(0.4, 0.1,0, 0.6, 0.9,0,0,0,1), ncol = 3)


#Move pops to here.
pops = c(250, 150, 50) #imagine the populations are like this (the commuter belt is larger in pop than the big city)

print(flow_matrix)

#what this says, is that theres three areas. The first area sends 60% of its people to the second area; and only 40% stay where they live.
#The second area sends 10% of its people to the first area, but 90% stay where they live.
#More practically, this is like one msoa thats a rural commuter belt, and another thats the central city. 
#People commute from the commuter belt to the city, but not so much the other way around.
#and then theres a third town, it sticks to itself

#To to do this, need to use transpose of flow_matrix as written above
flow_matrix = t(flow_matrix)
print(flow_matrix%*%pops)


#convert this to net flow
flow_matrix_net = flow_matrix - t(flow_matrix)
#This isn't the right net flow, if populations are unequal.
#We said  60% of the 250 in first area move to second. (150). And 10% of 150 move back (150)

actaul_flow_counts = t(flow_matrix)*pops
net_flow_counts = actaul_flow_counts - t(actaul_flow_counts)

flow_matrix_net = t(net_flow_counts/pops+diag(3))
flow_matrix_net_no_diag = t(net_flow_counts/pops)

#This then gives us the expected end result
print(flow_matrix_net%*%pops)

#anyway lets get the eignevectors for the flow, which splits this up
print(eigen((flow_matrix)))
#Has first 2 areas showing some overlap, and the third on its own.

#Vector 3 is telling us about moving from area 1 to area 2. This has lowest eigenvalue though
#Vector 2 is telling us about people staying in area 3.
#Vector 1 is telling us *something* is connected between areas 1 and 2?
#No, this is just a 1:6 ratio -- from 10% of people leaving area 1 vs 60% leaving area 2.


#And the net flow
print(eigen((flow_matrix_net)))
#Okay, here we see both the real and imag parts are important to say that EV1 and EV2 are non-zero in 1st 2 elements.
#Shit --- need both here.

#Here, vectors 1 and 2 are telling us the same thing (link between areas 1 and 2).
#vector 3 is telling us people stay is area 3.
#Here, the highest (magnitude) eigenvector is the interesting part.

#The eigenvalue is sqrt(-135/250 * 135/150) : net flow is 135, with 150 and 250 starting is areas 1 and 2.
#Value of the eigenvectors here are a ratio of i* sqrt(5/3). Is this just 250/150 for the starting populations? Yes -- tried changing the values to 250/200 and it is.

#So what?
#We have a EV of net flow /(sqrt(area 1 pop * area 2 pop))
#And can write our eigenvectors as 
# (1/sqrt(area 1 pop), +/- i/sqrt(area 2 pop), 0)


#Quick check -- without the diagonal (which we do need to reproduce expected final vector), eigenvectors and the same
print(eigen((flow_matrix_net_no_diag)))
#OK, at least that's true.

vec1=eigen((flow_matrix))$vectors[,1]
vec2=eigen((flow_matrix))$vectors[,2]
vec3=eigen((flow_matrix))$vectors[,3]
print(sum(vec1*vec1))

#Note -- modulus of all these vectors is 1 (but for complex, we do need the real and imag for this.

