# ICD Tokenizer

Base on a description of cause of death, extract the key word.

## Prerequisite

### Environment

Create your python virtual environment with. You can choose any tool to create.

```shell
conda env create -f environment.yml --prefix ./env
conda activate ./env
```

## Run

```shell
python main.py
```

## Result

| Name                        | Correct / Total | Accuracy |
|:---------------------------:|:---------------:|:--------:|
| 1110217_斷字比對(11101).xlsx | 13185 / 14734   | 89.48%   |
| 1110316_斷字比對(11102).xlsx | 13470 / 15059   | 89.44%   |
| 1110420_斷字比對(11103).xlsx | 15145 / 16956   | 89.31%   |
| 1110523_斷字比對(11104).xlsx | 12085 / 13478   | 89.66%   |
| 1110623_斷字比對(11105).xlsx | 14750 / 16556   | 89.09%   |
| 1110727_斷字比對(11106).xlsx | 16628 / 18789   | 88.49%   |
| 1110829_斷字比對(11107).xlsx | 14744 / 16552   | 89.07%   |
| 1110922_斷字比對(11108).xlsx | 13722 / 15331   | 89.50%   |
| 1111025_斷字比對(11109).xlsx | 14506 / 16251   | 89.26%   |
| 1111121_斷字比對(11110).xlsx | 14452 / 16123   | 89.63%   |
| 1120109_斷字比對(11111).xlsx | 13952 / 15548   | 89.73%   |
| 1120206_斷字比對(11112).xlsx | 15053 / 16797   | 89.61%   |
| 1120215_斷字比對(11201).xlsx | 15637 / 17356   | 90.09%   |
| 1120324_斷字比對(11202).xlsx | 16371 / 18139   | 90.25%   |
