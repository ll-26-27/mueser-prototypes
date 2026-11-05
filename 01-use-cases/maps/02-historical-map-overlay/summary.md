# Historical map overlay: summary

**Purpose.** Put a georeferenced historical map under the points, and show
how to find and check one.

**Workflow.** Query the Allmaps index at each resolved point; compute each
sheet's scale from its control points; test whether the control-point box
contains the point.

**Findings.** 4,200 matches, nine at regional or city scale, none sound for
this route. The toggle is therefore off by default, and the table shows why.

**Next.** Georeference one Prussian provincial map in the Allmaps editor;
paste the annotation URL into `.env`; rebuild.
