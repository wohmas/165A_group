from BTrees.OOBTree import OOBTree

# create_tree() {
# Create a tree when a new table is created
# 
# }

# update_tree() {
# When Query Update is called, replace existing values for relevant key
# 
# }


s = OOBTree()
for x in range(1, 1000):
  s.update({x: "RID" + str(x)}) 
print(s[369])