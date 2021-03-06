package agent;

import graph.Node;

import java.util.ArrayList;
import java.util.List;

import model.DefenderAction;
import model.DefenderBelief;
import model.DefenderObservation;
import model.DependencyGraph;

import org.apache.commons.math3.distribution.UniformIntegerDistribution;
import org.apache.commons.math3.random.RandomGenerator;

public final class MinCutDefender extends Defender {
	private int maxNumRes;
	private int minNumRes;
	private double numResRatio;
	private double numCandStdev;
	
	public MinCutDefender(
		final double maxNumRes, 
		final double minNumRes, 
		final double numResRatio,
		final double numCandStdev) {
		super(DefenderType.MINCUT);
		if (maxNumRes < minNumRes || minNumRes < 0 || !isProb(numResRatio)
			|| numCandStdev < 0.0) {
			throw new IllegalArgumentException();
		}
		this.maxNumRes = (int) maxNumRes;
		this.minNumRes = (int) minNumRes;
		this.numResRatio = numResRatio;
		this.numCandStdev = numCandStdev;
	}
	
	@Override
	public DefenderAction sampleAction(
		final DependencyGraph depGraph,
		final int curTimeStep,
		final int numTimeStep,
		final DefenderBelief dBelief,
		final RandomGenerator rng
	) {
		if (depGraph == null || curTimeStep < 0 || numTimeStep < curTimeStep || dBelief == null || rng == null) {
			throw new IllegalArgumentException();
		}
		List<Node> dCandidateNodeList = new ArrayList<Node>(depGraph.getMinCut());
		final int goalCount =
			(int) (dCandidateNodeList.size() * this.numResRatio + rng.nextGaussian() * this.numCandStdev);
		final int numNodetoProtect =
			Attacker.getActionCount(this.minNumRes, this.maxNumRes, dCandidateNodeList.size(), goalCount);
		if (dCandidateNodeList.size() == 0) {
			return new DefenderAction();
		}
		// Sample nodes
		UniformIntegerDistribution rnd = new UniformIntegerDistribution(rng, 0, dCandidateNodeList.size() - 1);
		return simpleSampleAction(dCandidateNodeList, numNodetoProtect, rnd);	
	}
	
	@Override
	public DefenderBelief updateBelief(
		final DependencyGraph depGraph,
		final DefenderBelief currentBelief, 
		final DefenderAction dAction,
		final DefenderObservation dObservation, 
		final int curTimeStep, 
		final int numTimeStep,
		final RandomGenerator rng) {
		return new DefenderBelief(); // empty belief
	}
	
	public int getMaxNumRes() {
		return this.maxNumRes;
	}

	public int getMinNumRes() {
		return this.minNumRes;
	}

	public double getNumResRatio() {
		return this.numResRatio;
	}

	public double getNumCandStdev() {
		return this.numCandStdev;
	}

	@Override
	public String toString() {
		return "MinCutDefender [maxNumRes=" + this.maxNumRes + ", minNumRes="
			+ this.minNumRes + ", numResRatio=" + this.numResRatio + ", numCandStdev="
			+ this.numCandStdev + "]";
	}
}
