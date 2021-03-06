package lpwrapper;

import ilog.concert.IloColumn;
import ilog.concert.IloException;
import ilog.concert.IloNumExpr;
import ilog.concert.IloNumVar;
import ilog.concert.IloNumVarType;
import ilog.concert.IloRange;
import ilog.cplex.CpxException;
import ilog.cplex.IloCplex;
import ilog.cplex.IloCplex.CplexStatus;
import ilog.cplex.IloCplex.UnknownObjectException;

import java.io.OutputStream;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import game.GameSimulation;

public abstract class MIProblemCplex extends AMIProblem {
	protected IloCplex cplex;
	// IloObjective objectiveFunction;

	protected List<IloNumVar> columns;
	protected Map<Integer, IloRange> rows;

	protected Map<Integer, RowStatus> rowsInModel;
	protected List<Double> objectiveCoeff;
	protected List<IloNumVarType> columnType;

	protected IloCplex.BasisStatus[] colStatuses;
	protected IloCplex.BasisStatus[] rowStatuses;

	protected boolean objectiveModified;
	
	@Override
	protected final void initialize() {
		try {
			if (this.cplex != null) {
				this.cplex.end();
			}
			this.objectiveModified = false;
			this.cplex = new IloCplex();
			this.cplex.setName("MIProblem");
			// objectiveFunction = cplex.getObjective();
			// cplex.setParam(IloCplex.IntParam.RootAlg, IloCplex.Algorithm.Dual);
			// cplex.setParam(IloCplex.IntParam.RootAlg, IloCplex.Algorithm.Primal);
			// cplex.setParam(IloCplex.IntParam.RootAlg, IloCplex.Algorithm.Barrier);
			// cplex.setParam(IloCplex.DoubleParam.EpMrk, 0.999);
			this.redirectOutput(null);
		} catch (IloException e) {
			e.printStackTrace();
			throw new RuntimeException(e.getMessage());
		}
		this.columns = new ArrayList<IloNumVar>(this.numCols);
		this.rows = new HashMap<Integer, IloRange>(this.numRows);
		this.rowsInModel = new HashMap<Integer, MIProblemCplex.RowStatus>(
				this.numRows);
		this.objectiveCoeff = new ArrayList<Double>(this.numCols);
		this.columnType = new ArrayList<IloNumVarType>(this.numCols);
		this.colStatuses = null;
		this.rowStatuses = null;
	}

	@Override
	public final StatusType getSolveStatus() {
		CplexStatus cplexStat;
		try {
			cplexStat = this.cplex.getCplexStatus();
			if (cplexStat == CplexStatus.Optimal || cplexStat == CplexStatus.OptimalTol) {
				return StatusType.OPTIMAL;
			} else if (cplexStat == CplexStatus.Infeasible) {
				return StatusType.INFEASIBLE;
			} else if (cplexStat == CplexStatus.Unbounded) {
				return StatusType.UNBOUNDED;
			} else {
				// GameSimulation.printIfDebug("Cplex Status: " + cplex.getCplexStatus());
				return StatusType.UNKNOWN;
			}
		} catch (IloException e) {
			e.printStackTrace();
			throw new RuntimeException("Unable to get cplex status.");
		}
	}

	public MIProblemCplex() {
		super();
		this.cplex = null;
		this.initialize();
	}

	@Override
	protected final void setProblemName(final String name) {
		this.cplex.setName(name);
	}

// public void writeProb(String fileName) {
//        try {
//            cplex.exportModel(fileName + ".lp");
//        } catch (IloException e) {
//            e.printStackTrace();
//            throw new RuntimeException(e.getMessage());
//        }
//    }

	@Override
	protected final void setObjectiveCoef(final int index, final double value) {
		this.objectiveModified = true;
		this.objectiveCoeff.set(index - 1, value);
	}

	protected final double getObjectiveCoef(final int index) {
		return this.objectiveCoeff.get(index - 1);
	}

	/**
	 * Returns the number of iterations in the last solve.
	 * 
	 * @return
	 */
	@Override
	public final int getNumberIterations() {
		return this.cplex.getNiterations();
	}

	/**
	 * Returns the number of MIP starts associated with the current problem.
	 * 
	 * @return
	 */
	@Override
	public final int getMIPStarts() {
		try {
			return this.cplex.getNMIPStarts();
		} catch (IloException e) {
			e.printStackTrace();
			throw new RuntimeException("MIP starts could not be obtained.");
		}
	}

	/**
	 * Returns the no. of branch-and-cut nodes explored in solving the active
	 * model.
	 * 
	 * @return
	 */
	@Override
	public final int getNodesExplored() {
		return this.cplex.getNnodes();
	}

	/**
	 * Returns the number of unexplored nodes in the branch-and-cut tree.
	 * 
	 * @return
	 */
	@Override
	public final int getNodesLeft() {
		return this.cplex.getNnodesLeft();
	}

	/**
	 * Returns the number of phase I simplex iterations from the last solve.
	 * 
	 * @return
	 */
	@Override
	public final int getSimplexIterations() {
		return this.cplex.getNphaseOneIterations();
	}

	@Override
	public final void resetColumnBound(final int columnNumber, final BoundsType boundType,
		final double lowerBound, final double upperBound) {
		try {
			switch (boundType) {
			case FREE:
				this.columns.get(columnNumber - 1).setLB(-Configuration.MM);
				this.columns.get(columnNumber - 1).setUB(Configuration.MM);
				break;
			case LOWER:
				this.columns.get(columnNumber - 1).setLB(-Configuration.MM);
				this.columns.get(columnNumber - 1).setUB(Configuration.MM);
				this.columns.get(columnNumber - 1).setLB(lowerBound);
				break;
			case UPPER:
				this.columns.get(columnNumber - 1).setLB(-Configuration.MM);
				this.columns.get(columnNumber - 1).setUB(Configuration.MM);
				this.columns.get(columnNumber - 1).setUB(upperBound);
				break;
			case DOUBLE:
				this.columns.get(columnNumber - 1).setLB(-Configuration.MM);
				this.columns.get(columnNumber - 1).setUB(Configuration.MM);
				this.columns.get(columnNumber - 1).setLB(lowerBound);
				this.columns.get(columnNumber - 1).setUB(upperBound);
				break;
			case FIXED:
				this.columns.get(columnNumber - 1).setLB(-Configuration.MM);
				this.columns.get(columnNumber - 1).setUB(Configuration.MM);
				this.columns.get(columnNumber - 1).setLB(lowerBound);
				this.columns.get(columnNumber - 1).setUB(lowerBound);
				break;
			default:
				throw new RuntimeException("No such bound type.");
			}
		} catch (IloException e) {
			e.printStackTrace();
			throw new RuntimeException("Column Number is wrong.");
		}
	}

	@Override
	protected final void setProblemType(final ProblemType problemType,
			final ObjectiveType objectiveType) {
		this.probType = problemType;
		this.objectiveType = objectiveType;
		try {
			this.updateObjective();
		} catch (Exception e) {
			e.printStackTrace();
			throw new RuntimeException("Update Objective Failed");
		}
	}

	@Override
	public final boolean disableRow(final int rowNumber) throws RuntimeException {
		try {
			if (this.rowsInModel.get(rowNumber - 1) == RowStatus.ENABLED) {
				this.cplex.remove(this.rows.get(rowNumber - 1));
				this.rowsInModel.put(rowNumber - 1, RowStatus.DISABLED);
				return true;
			}
		} catch (IloException e) {
			e.printStackTrace();
			throw new RuntimeException(e.getMessage());
		}
		return false;
	}

	public final boolean deleteRow(final int rowNumber) throws RuntimeException {
		try {
			if (this.rowsInModel.get(rowNumber - 1) == RowStatus.ENABLED) {
				this.cplex.remove(this.rows.get(rowNumber - 1));
				this.rows.remove(rowNumber - 1);

				return true;
			}
		} catch (IloException e) {
			e.printStackTrace();
			throw new RuntimeException(e.getMessage());
		}
		return false;
	}

	@Override
	public final void importFile(final String fileName) {
		try {
			this.cplex = new IloCplex();
			this.cplex.importModel(fileName);
		} catch (IloException e) {
			e.printStackTrace();
			throw new RuntimeException("Error reading file");
		}
	}

	@Override
	public final boolean enableRow(final int rowNumber) throws RuntimeException {
		try {
			if (this.rowsInModel.get(rowNumber - 1) == RowStatus.DISABLED) {
				this.cplex.add(this.rows.get(rowNumber - 1));
				this.rowsInModel.put(rowNumber - 1, RowStatus.ENABLED);
				return true;
			}
		} catch (IloException e) {
			e.printStackTrace();
			throw new RuntimeException(e.getMessage());
		}
		return false;
	}

	private IloNumExpr getObjectiveFunction() throws IloException {
		Double[] objCoefDblObj = this.objectiveCoeff.toArray(new Double[] {});
		double[] objCoeffDblBasicType = new double[objCoefDblObj.length];
		for (int i = 0; i < objCoefDblObj.length; i++) {
			double val = objCoefDblObj[i].doubleValue();
			if (Math.abs(val) < Configuration.EPSILON) {
				val = 0.0;
			}
			objCoeffDblBasicType[i] = val;
		}
		return (this.cplex.scalProd(this.columns.toArray(new IloNumVar[] {}),
				objCoeffDblBasicType));
	}

	public final void removeObjective() {
		try {
			this.cplex.delete(this.cplex.getObjective());
			for (int i = 0; i < this.objectiveCoeff.size(); i++) {
				this.objectiveCoeff.set(i, 0.0);
			}
		} catch (IloException e) {
			e.printStackTrace();
			throw new RuntimeException("Couldn't delete objective.");
		}
	}
	
	@Override
	public final void updateObjective() throws Exception {
		IloNumExpr objectiveFunctionExpr = this.getObjectiveFunction();

		this.cplex.delete(this.cplex.getObjective());
		switch (this.objectiveType) {
		case MAX:
			this.cplex.addMaximize(objectiveFunctionExpr);
			break;
		case MIN:
			this.cplex.addMinimize(objectiveFunctionExpr);
			break;
		default:
			throw new IllegalArgumentException("I don't know this type, kid!");
		}
	}

	@Override
	public final void addAndSetColumn(final String name, final BoundsType boundType,
		final double lowerBound, final double upperBound, final VariableType varType,
		final double objCoeff) {
		try {
			// IloColumn newCol = cplex.column(this.objectiveFunction,
			// objCoeff);
			IloNumVar col;
			switch (varType) {
			case CONTINUOUS:
				col = this.cplex.numVar(lowerBound, upperBound, IloNumVarType.Float,
						name);
				this.columnType.add(IloNumVarType.Float);
				break;
			case INTEGER:
				col = this.cplex.numVar(lowerBound, upperBound, IloNumVarType.Int,
						name);
				this.columnType.add(IloNumVarType.Int);
				break;
			default:
				throw new IllegalArgumentException("Unknown Variable Type");
			}
			this.columns.add(col);
			this.objectiveCoeff.add(objCoeff);
			this.numCols++;

			this.updateObjective();
		} catch (Exception e) {
			e.printStackTrace();
			throw new RuntimeException(e.getMessage());
		}
	}

	@Override
	public final void resetRowBound(final int rowNumber, final BoundsType boundType,
		final double lowerBound, final double upperBound) {
		try {
			/*
			 * this.rows.get(rowNumber - 1).setLB(-Configuration.MM);
			 * this.rows.get(rowNumber - 1).setUB(Configuration.MM);
			 */
			switch (boundType) {
			case LOWER:
				this.rows.get(rowNumber - 1).setLB(-Double.MAX_VALUE);
				this.rows.get(rowNumber - 1).setUB(Double.MAX_VALUE);
				this.rows.get(rowNumber - 1).setLB(lowerBound);
				break;
			case UPPER:
				this.rows.get(rowNumber - 1).setLB(-Double.MAX_VALUE);
				this.rows.get(rowNumber - 1).setUB(Double.MAX_VALUE);
				this.rows.get(rowNumber - 1).setUB(upperBound);
				break;
			case DOUBLE:
				this.rows.get(rowNumber - 1).setLB(-Double.MAX_VALUE);
				this.rows.get(rowNumber - 1).setUB(Double.MAX_VALUE);
				this.rows.get(rowNumber - 1).setLB(lowerBound);
				this.rows.get(rowNumber - 1).setUB(upperBound);
				break;
			case FIXED:
				this.rows.get(rowNumber - 1).setLB(-Double.MAX_VALUE);
				this.rows.get(rowNumber - 1).setUB(Double.MAX_VALUE);
				this.rows.get(rowNumber - 1).setLB(lowerBound);
				this.rows.get(rowNumber - 1).setUB(lowerBound);
				break;
			default:
				throw new RuntimeException("No such bound type.");
			}
		} catch (IloException e) {
			e.printStackTrace();
			throw new RuntimeException("Row Number is wrong. (row number = "
					+ rowNumber + ")");
		}

	}

	@Override
	public final int addAndSetRow(final String name, final BoundsType boundType,
		final double lowerBound, final double upperBound) {
		try {
			IloRange newRow;
			IloNumExpr rowExpr = this.cplex.constant(0.0);
			switch (boundType) {
			case UPPER:
				newRow = this.cplex.addGe(upperBound, rowExpr, name);
				break;
			case LOWER:
				newRow = this.cplex.addLe(lowerBound, rowExpr, name);
				break;
			case FIXED:
				newRow = this.cplex.addEq(lowerBound, rowExpr, name);
				break;
			default:
				throw new IllegalArgumentException("Unknown Type");
			}
			this.rows.put(this.numRows, newRow);
			this.rowsInModel.put(this.numRows, RowStatus.ENABLED);
			this.numRows++;
		} catch (IloException e) {
			e.printStackTrace();
			throw new RuntimeException("Error in Set Row: "
					+ (this.numRows + 1));
		}
		return this.rows.size();
	}

	/**
	 * adds a new column and initializes it
	 * 
	 * @param name
	 * @param varType
	 * @param objCoeff
	 * @param lowerBound
	 * @param upperBound
	 * @param indices
	 * @param values
	 * @throws RuntimeException
	 */
	@Override
	public final void setMatCol(final String name, final VariableType varType, final double objCoeff,
		final double lowerBound, final double upperBound, final List<Integer> indices,
		final List<Double> values) throws RuntimeException {
		// do addColumn
		// setColumn
		// setMatCol
		IloColumn newColumn;
		try {
			newColumn = this.cplex.column(this.cplex.getObjective(), objCoeff);
			for (int i = 0; i < indices.size(); i++) {
				newColumn = newColumn.and(this.cplex.column(
						this.rows.get(indices.get(i) - 1), values.get(i)));
			}
			IloNumVar col;
			switch (varType) {
			case CONTINUOUS:
				col = this.cplex.numVar(newColumn, lowerBound, upperBound,
						IloNumVarType.Float, name);
				this.columnType.add(IloNumVarType.Float);
				break;
			case INTEGER:
				col = this.cplex.numVar(newColumn, lowerBound, upperBound,
						IloNumVarType.Int, name);
				this.columnType.add(IloNumVarType.Int);
				break;
			default:
				throw new IllegalArgumentException("Unknown Variable Type");
			}
			this.objectiveCoeff.add(objCoeff);
			this.columns.add(col);
			this.numCols++;
		} catch (IloException e) {
			e.printStackTrace();
			throw new RuntimeException(e.getMessage());
		}
	}

	/**
	 * Doesn't add a new row
	 */
	@Override
	public final void setMatRow(final int rowNo, final List<Integer> indices, final List<Double> values)
		throws RuntimeException {
		if (indices.size() != values.size()) {
			throw new RuntimeException();
		}
		IloNumExpr constraintExpr;
		try {
			constraintExpr = this.cplex.constant(0.0);
			for (int i = 0; i < indices.size(); i++) {
				constraintExpr = this.cplex.sum(
						constraintExpr,
						this.cplex.prod(values.get(i).doubleValue(),
								this.columns.get(indices.get(i) - 1)));
			}
			this.rows.get(rowNo - 1).setExpr(constraintExpr);
		} catch (Exception e) {	
			// GameSimulation.printIfDebug("rowNo: " + rowNo);
			// GameSimulation.printIfDebug(rows.size());
			// GameSimulation.printIfDebug(rows.get(rowNo - 1));
			
			e.printStackTrace();
			
			// System.exit(1); // Manish
			
			throw new RuntimeException(e.getMessage());						
		}
	}

	@Override
	protected final void saveBasisStatus() {
		if (!Configuration.WARMSTARTLPS || this.columns.size() == 0
			|| this.rows.size() == 0 || this.probType == ProblemType.MIP) {
			return;
		}
		try {
			// IloLPMatrix lp = (IloLPMatrix)cplex.LPMatrixIterator().next();
			// IloNumVar[] vars = lp.getNumVars();
			// colStatuses = cplex.getBasisStatuses(vars);
			this.colStatuses = this.cplex.getBasisStatuses(this.columns
					.toArray(new IloNumVar[] {}));
			this.rowStatuses = this.cplex.getBasisStatuses(this.rows.values().toArray(
					new IloRange[] {}));
		} catch (IloException e) {
			e.printStackTrace();
			System.err.println("Save Basis Failed: " + e.getMessage());
			this.colStatuses = null;
			this.rowStatuses = null;
			throw new RuntimeException(e.getMessage());
		}
	}

	@Override
	protected final void loadBasisStatus() {
		if (!Configuration.WARMSTARTLPS || this.colStatuses == null
				|| this.rowStatuses == null || this.probType == ProblemType.MIP) {
			return;
		}
		try {
			this.cplex.setBasisStatuses(this.columns.toArray(new IloNumVar[] {}),
					this.colStatuses, 0, this.colStatuses.length, this.rows.values()
							.toArray(new IloRange[] {}), this.rowStatuses, 0,
							this.rowStatuses.length);
		} catch (IloException e) {
			e.printStackTrace();
			System.err.println("Load Basis Failed: " + e.getMessage());
			this.colStatuses = null;
			this.rowStatuses = null;
			throw new RuntimeException(e.getMessage());
		}
	}

	@Override
	public final void solve() throws LPSolverException {	
		if (!this.isLoaded) {
			this.loadProblem();
		}
		if (this.objectiveModified) {
			try {
				this.updateObjective();
			} catch (Exception e) {
				e.printStackTrace();
				throw new LPSolverException();				
			}
			this.objectiveModified = false;
		}
		long start = System.currentTimeMillis();
		try {
			this.updateObjective();
			this.loadBasisStatus();
			boolean retval = this.cplex.solve();
			// MANISH DEBUG PRINT
			// cplex.getCplexStatus().equals(CplexStatus.Optimal)
			if (!retval /*
								 * ||
								 * !cplex.getCplexStatus().equals(CplexStatus.
								 * Optimal)
								 */) {
				// writeProb("CPLEXfail");
				if (Configuration.PRINT_ERROR) {
					System.err.println("CPLEX error: " + this.cplex.getObjValue()
							+ ";" + this.cplex.getCplexStatus());
				}
				throw new LPSolverException();
			}
			this.saveBasisStatus();
		} catch (Exception e) {
			this.runTime = System.currentTimeMillis() - start;
			if (Configuration.PRINT_ERROR) {
				e.printStackTrace();
			}
			throw new LPSolverException();
		}
		this.runTime = System.currentTimeMillis() - start;
	}

	@Override
	public final double getRowDual(final int rowNumber) {
		try {
			double dual = this.cplex.getDual(this.rows.get(rowNumber - 1));
			return dual;
		} catch (UnknownObjectException e) {
			e.printStackTrace();
			throw new RuntimeException(e.getMessage());
		} catch (IloException e) {
			e.printStackTrace();
			throw new RuntimeException(e.getMessage());
		}
	}

	@Override
	public final double getRowSlack(final int rowNumber) {
		try {
			return this.cplex.getSlack(this.rows.get(rowNumber - 1));
		} catch (UnknownObjectException e) {
			e.printStackTrace();
			throw new RuntimeException(e.getMessage());
		} catch (IloException e) {
			e.printStackTrace();
			throw new RuntimeException(e.getMessage());
		}
	}

	@Override
	public final double getColumnPrimal(final int columnNumber) {
		double xVal;
		try {
			xVal = this.cplex.getValue(this.columns.get(columnNumber - 1));
			return xVal;
		} catch (UnknownObjectException e) {
			e.printStackTrace();
			throw new RuntimeException(e.getMessage());
		} catch (CpxException e) {
			e.printStackTrace();
			return 0.0;
		} catch (IloException e) {
			e.printStackTrace();
			throw new RuntimeException(e.getMessage());
		}

	}

	@Override
	public final List<Double> getRowDualVector() {
		double[] duals;
		try {
			duals = this.cplex.getDuals(this.rows.values().toArray(new IloRange[] {}));
			List<Double> dualVect = new ArrayList<Double>(duals.length);
			for (int i = 0; i < duals.length; i++) {
				dualVect.add(duals[i]);
			}
			return dualVect;
		} catch (UnknownObjectException e) {
			e.printStackTrace();
			throw new RuntimeException(e.getMessage());
		} catch (IloException e) {
			e.printStackTrace();
			throw new RuntimeException(e.getMessage());
		}
	}

	@Override
	public final List<Double> getColumnPrimalVector() {
		try {
			double[] xVals = this.cplex.getValues(this.columns
					.toArray(new IloNumVar[] {}));
			List<Double> primalVect = new ArrayList<Double>(xVals.length);
			for (int i = 0; i < xVals.length; i++) {
				primalVect.add(xVals[i]);
			}
			return primalVect;
		} catch (UnknownObjectException e) {
			e.printStackTrace();
			throw new RuntimeException(e.getMessage());
		} catch (IloException e) {
			e.printStackTrace();
			throw new RuntimeException(e.getMessage());
		}
	}

	@Override
	public final double getLPObjective() {
		try {
			return this.cplex.getObjValue();
		} catch (IloException e) {
			e.printStackTrace();
			throw new RuntimeException(e.getMessage());
		}
	}

	@Override
	public final void writeProb(final String fileName) {
		try {
			this.cplex.exportModel(fileName + ".lp");
		} catch (IloException e) {
			e.printStackTrace();
			throw new RuntimeException(e.getMessage());
		}
	}

	@Override
	public final void writeSol(final String fileName) {
		try {
			this.cplex.writeSolution(fileName);
		} catch (IloException e) {
			e.printStackTrace();
			throw new RuntimeException(e.getMessage());
		}
	}

	/**
	 * clean the data structures.
	 */
	@Override
	public final void end() {
		this.cplex.end();
		this.columns.clear();
		this.rows.clear();
		this.objectiveCoeff.clear();
		this.columnType.clear();
		this.colStatuses = null;
		this.rowStatuses = null;
	}

	/**
	 * 
	 * @param stream
	 *            can be <code>null</code> if no output should be provided.
	 */
	@Override
	public final void redirectOutput(final OutputStream stream) {
		this.cplex.setOut(stream);
		this.cplex.setWarning(stream);
	}

	@Override
	public final double getRowPrimal(final int rowNumber) {
		try {
			return this.cplex.getValue(this.rows.get(rowNumber - 1).getExpr());
		} catch (IloException e) {
			e.printStackTrace();
			throw new RuntimeException(e.getMessage());
		}
	}
}
