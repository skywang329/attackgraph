package model;

import graph.Node;

import java.util.HashSet;
import java.util.Set;

public class DefenderCandidate {
	Set<Node> nodeCandidateSet; // for AND node
	public DefenderCandidate()
	{
		this.nodeCandidateSet = new HashSet<Node>();
	}
	
	public boolean addNodeCandidate(Node node){
		return this.nodeCandidateSet.add(node);
	}
	public Set<Node> getNodeCandidateSet(){
		return this.nodeCandidateSet;
	}
	public void clear(){
		this.nodeCandidateSet.clear();
	}
}