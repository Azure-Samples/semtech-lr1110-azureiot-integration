Connect-AzAccount

Get-AzContext -ListAvailable

$name= Read-Host -Prompt "Enter your subscription name"

Set-AzContext -Subscription $name

$RGname= Read-Host -Prompt "Enter resource group name"

New-AzResourceGroup -Name $RGname -Location "West Europe"

$today=Get-Date -Format "MM-dd-yyyy"
$deploymentName="IoTDeployment"+"$today"

New-AzResourceGroupDeployment `
  -Name $deploymentName `
  -ResourceGroupName $RGname  `
  -TemplateFile '.\azuredeployBasic.json' `
  -Verbose
  