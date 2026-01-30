def attach_hype_score(objects):
    for obj in objects:
        excited = getattr(obj, "excited_count", 0)  #if obj.excited_count exist then → use  else 0 
        total = getattr(obj, "total_hype_votes", 0)

        if total > 0:
            obj.hype_score = round((excited / total) * 100)
        else:
            obj.hype_score = 0
    return objects
