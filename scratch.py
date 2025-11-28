

import pandas as pd

df = pd.read_csv("benchmarks/xcsp3_ortools.csv")

# AllDifferent=BinaryDecomposedAllDifferent,
# Cumulative=TaskDecomposedCumulative,
# NoOverlap=BinaryDecomposedNoOverlap,
# NonReifiedTable=DecomposedTable,
# NonReifiedNegativeTable=DecomposedNegativeTable,
# Regular=DecomposedRegular,
# Inverse=DecomposedInverse

df = df.drop(columns=['InDomain',
                      'alldifferent_except_n',
                      'alldifferent_lists',
                      'channelValue',
                      'decreasing','gcc','increasing','lex_chain_lesseq','no_overlap2d','precedence','short_table',
                      'strictly_increasing','subcircuitwithstart'])

df = df.fillna(0)
df['num_globals'] = df['alldifferent'] + df['cumulative'] + df['negative_table'] + df['regular'] + df['table'] + df['inverse'] + df['no_overlap']

print(df[df['num_globals'] > 0])